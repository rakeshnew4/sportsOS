"""Smart match recommendations based on player profile and history."""

from datetime import datetime

from app.core.db import Client, FieldFilter
from app.services import booking_service, match_service, kpi_service
from app.models.kpi import PlayerKPIScope


def get_player_recommendations_with_llm(db: Client, uid: str, limit: int = 5) -> list[dict]:
    """
    Get recommendations using LLM for smarter matching.
    Falls back to rule-based if LLM fails.
    """
    try:
        from app.services.llm_service import generate_recommendations

        # Get player profile
        try:
            kpi = kpi_service.get_player_engagement_kpi(db, uid, PlayerKPIScope.ALL_TIME)
        except Exception:
            return get_player_recommendations(db, uid, limit)

        # Get available matches
        all_open_matches = match_service.discover_matches(db)

        # Prepare player history for LLM
        player_history = {
            "sports": [kpi.favorite_sport] if kpi.favorite_sport else [],
            "favorite_sport": kpi.favorite_sport,
            "skill_level": "intermediate",
            "preferred_time": "evening",
            "venues": [kpi.favorite_venue] if kpi.favorite_venue else [],
        }

        # Prepare available slots
        available_slots = [
            {
                "sport": m.sport,
                "venue": m.tenant_name,
                "date": m.date,
                "time": f"{m.start_time}–{m.end_time}",
                "players": m.slots_total - m.slots_open,
                "max_players": m.slots_total,
                "booking_id": m.booking_id,
            }
            for m in all_open_matches[:10]
        ]

        # Get LLM recommendations
        llm_scores = generate_recommendations(uid, player_history, available_slots)

        # Map LLM scores back to matches
        recommendations = []
        for scored_match in llm_scores:
            if scored_match["match_index"] < len(all_open_matches):
                m = all_open_matches[scored_match["match_index"]]
                recommendations.append({
                    "booking_id": m.booking_id,
                    "sport": m.sport,
                    "venue": m.tenant_name,
                    "date": m.date,
                    "time": f"{m.start_time}–{m.end_time}",
                    "slots": f"{m.slots_total - m.slots_open}/{m.slots_total}",
                    "score": scored_match["score"],
                    "reasons": [scored_match["reason"]],
                })

        recommendations.sort(key=lambda r: r["score"], reverse=True)
        return recommendations[:limit]
    except Exception:
        # Fallback to rule-based recommendations
        return get_player_recommendations(db, uid, limit)


def get_player_recommendations(db: Client, uid: str, limit: int = 5) -> list[dict]:
    """
    Recommend open matches based on player's profile:
    - Favorite sport & venue
    - Favorite time of day (from match history)
    - Match fill rate (close to being full = better chance to play soon)
    """

    # Get player's engagement data
    try:
        kpi = kpi_service.get_player_engagement_kpi(db, uid, PlayerKPIScope.ALL_TIME)
    except Exception:
        return []

    # Get player's match history to find favorite time of day
    bookings = booking_service.list_my_bookings(db, uid)
    confirmed = [b for b in bookings if b.status == "confirmed"]

    # Calculate favorite time of day (hour)
    hour_counts = {}
    for b in confirmed:
        try:
            hour = int(b.start_time.split(":")[0])
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        except (ValueError, IndexError):
            pass

    favorite_hour = max(hour_counts.keys(), default=18) if hour_counts else 18

    # Get all open matches
    all_open_matches = match_service.discover_matches(db)

    # Score each match based on:
    # 1. Sport match (favorite sport = +10 points)
    # 2. Time match (within 2 hours of favorite time = +5 points)
    # 3. Fill rate (60-80% full = +10, 80-90% = +5, >90% = +15 but risky)
    # 4. Venue match (favorite venue = +5)

    recommendations = []

    for match in all_open_matches:
        score = 0
        reasons = []

        # Sport match
        if kpi.favorite_sport and match.sport.lower() == kpi.favorite_sport.lower():
            score += 10
            reasons.append(f"Your favorite sport: {match.sport}")
        elif match.sport.lower() in ["badminton", "tennis", "table_tennis"]:  # Racquet sports
            score += 3
            reasons.append(f"Racquet sport: {match.sport}")

        # Time match
        try:
            match_hour = int(match.start_time.split(":")[0])
            hour_diff = abs(match_hour - favorite_hour)
            if hour_diff <= 2:
                score += 5
                reasons.append(f"Close to your favorite time ({favorite_hour}:00)")
            elif hour_diff <= 4:
                score += 2
        except (ValueError, IndexError):
            pass

        # Fill rate (games that are nearly full fill faster)
        if match.slots_total > 0:
            fill_pct = (match.slots_total - match.slots_open) / match.slots_total * 100
            if 60 <= fill_pct < 80:
                score += 10
                reasons.append(f"Good match: {int(fill_pct)}% full, {match.slots_open} slot(s) left")
            elif 80 <= fill_pct < 90:
                score += 5
                reasons.append(f"Almost full: {int(fill_pct)}% full")
            elif fill_pct >= 90:
                score += 15
                reasons.append(f"Play soon! {int(fill_pct)}% full, forming shortly")

        # Venue match
        if kpi.favorite_venue and match.tenant_name and kpi.favorite_venue.lower() in match.tenant_name.lower():
            score += 5
            reasons.append(f"Your favorite venue: {match.tenant_name}")

        if score > 0:
            recommendations.append({
                "booking_id": match.booking_id,
                "sport": match.sport,
                "venue": match.tenant_name,
                "date": match.date,
                "time": f"{match.start_time}–{match.end_time}",
                "slots": f"{match.slots_total - match.slots_open}/{match.slots_total}",
                "score": score,
                "reasons": reasons,
            })

    # Sort by score descending
    recommendations.sort(key=lambda r: r["score"], reverse=True)
    return recommendations[:limit]


def get_trending_sports(db: Client, tenant_id: str = None) -> list[dict]:
    """Get trending sports in the system (or at a specific venue)."""
    if tenant_id:
        # Venue-level trends
        bookings = booking_service.list_bookings(db, tenant_id)
    else:
        # System-level trends: get all bookings across all venues
        bookings = []
        for tenant_doc in db.collection("tenants").stream():
            try:
                venue_bookings = booking_service.list_bookings(db, tenant_doc.id)
                bookings.extend(venue_bookings)
            except Exception:
                pass

    # Count by sport
    sport_counts = {}
    for b in bookings:
        if b.status == "confirmed":
            sport = b.sport or "Unknown"
            sport_counts[sport] = sport_counts.get(sport, 0) + 1

    # Return sorted by count
    trends = [{"sport": s, "bookings": c} for s, c in sport_counts.items()]
    trends.sort(key=lambda t: t["bookings"], reverse=True)
    return trends
