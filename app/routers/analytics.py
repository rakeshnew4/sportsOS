from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Client, FieldFilter, get_db
from app.core.security import CurrentUser, get_current_user
from app.services import booking_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


class MatchHistory(BaseModel):
    booking_id: str
    date: str
    sport: str
    start_time: str
    end_time: str
    venue_name: str
    participants_count: int
    price_paid: float
    status: str


class MatchStats(BaseModel):
    total_matches: int
    matches_this_month: int
    matches_this_week: int
    favorite_sport: str | None
    favorite_day_of_week: str | None
    avg_participants: float = 0.0


class SportActivityTrend(BaseModel):
    sport: str
    week_starting: str
    matches_count: int
    hours_played: float
    total_revenue: float


@router.get("/players/me/match-history")
def get_my_match_history(
    limit: int = 20,
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> list[MatchHistory]:
    """Get history of all matches/bookings for current player."""
    my_bookings = booking_service.list_my_bookings(db, user.uid)

    results = []
    for booking in my_bookings:
        if booking.status != "confirmed":
            continue

        # Get venue name
        venue_doc = db.collection("tenants").document(booking.tenant_id).get()
        venue_name = venue_doc.to_dict().get("name", booking.tenant_id) if venue_doc.exists else booking.tenant_id

        # Calculate price paid by this player (captain + joiners split the total)
        participants_ref = (
            db.collection("tenants").document(booking.tenant_id)
            .collection("bookings").document(booking.booking_id)
            .collection("participants")
        )
        participant_count = 1 + len(list(participants_ref.stream()))
        price_per_person = booking.price / participant_count

        results.append(
            MatchHistory(
                booking_id=booking.booking_id,
                date=booking.date,
                sport=booking.sport,
                start_time=booking.start_time,
                end_time=booking.end_time,
                venue_name=venue_name,
                participants_count=participant_count,
                price_paid=round(price_per_person, 2),
                status=booking.status,
            )
        )

    # Sort by date descending
    results.sort(key=lambda m: m.date, reverse=True)
    return results[:limit]


@router.get("/players/me/stats")
def get_my_match_stats(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> MatchStats:
    """Get aggregated match statistics for current player."""
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    # Get all-time stats
    all_time = kpi_service.get_player_engagement_kpi(db, user.uid, PlayerKPIScope.ALL_TIME)
    month = kpi_service.get_player_engagement_kpi(db, user.uid, PlayerKPIScope.MONTH)
    week = kpi_service.get_player_engagement_kpi(db, user.uid, PlayerKPIScope.QUARTER)  # Using QUARTER as proxy for week

    my_bookings = booking_service.list_my_bookings(db, user.uid)
    confirmed_bookings = [b for b in my_bookings if b.status == "confirmed"]

    # Calculate favorite day of week
    day_counts = {}
    for booking in confirmed_bookings:
        try:
            bdate = datetime.fromisoformat(booking.date)
            day_name = bdate.strftime("%A")
            day_counts[day_name] = day_counts.get(day_name, 0) + 1
        except (ValueError, TypeError):
            pass

    favorite_day = max(day_counts.keys(), key=lambda d: day_counts[d]) if day_counts else None

    # Calculate avg participants
    avg_participants = 0.0
    if confirmed_bookings:
        total_participants = 0
        for b in confirmed_bookings:
            participants_ref = (
                db.collection("tenants").document(b.tenant_id)
                .collection("bookings").document(b.booking_id)
                .collection("participants")
            )
            total_participants += 1 + len(list(participants_ref.stream()))
        avg_participants = total_participants / len(confirmed_bookings)

    return MatchStats(
        total_matches=all_time.matches_played,
        matches_this_month=month.matches_played,
        matches_this_week=week.matches_played,
        favorite_sport=all_time.favorite_sport,
        favorite_day_of_week=favorite_day,
        avg_participants=round(avg_participants, 1),
    )


@router.get("/venues/{tenant_id}/sport-trends")
def get_venue_sport_trends(
    tenant_id: str,
    weeks: int = 4,
    db: Client = Depends(get_db),
) -> list[SportActivityTrend]:
    """Get sport-wise activity trends for a venue over past N weeks."""
    from app.services import court_service

    bookings = booking_service.list_bookings(db, tenant_id)

    # Group by week and sport
    now = datetime.now()
    trends_by_week_sport = {}

    for booking in bookings:
        if booking.status != "confirmed":
            continue

        try:
            bdate = datetime.fromisoformat(booking.date)
        except (ValueError, TypeError):
            continue

        # Only include past N weeks
        if (now - bdate).days > weeks * 7:
            continue

        # Calculate week starting date (Monday)
        week_start = bdate - timedelta(days=bdate.weekday())
        week_key = week_start.date().isoformat()

        sport = booking.sport
        key = (week_key, sport)

        if key not in trends_by_week_sport:
            trends_by_week_sport[key] = {"matches": 0, "hours": 0.0, "revenue": 0.0}

        trends_by_week_sport[key]["matches"] += 1

        # Calculate hours played
        try:
            start_h, start_m = map(int, booking.start_time.split(":"))
            end_h, end_m = map(int, booking.end_time.split(":"))
            duration_hours = (end_h + end_m / 60) - (start_h + start_m / 60)
            trends_by_week_sport[key]["hours"] += duration_hours
        except (ValueError, AttributeError):
            pass

        trends_by_week_sport[key]["revenue"] += booking.price

    # Convert to response format
    results = []
    for (week_key, sport), data in sorted(trends_by_week_sport.items()):
        results.append(
            SportActivityTrend(
                sport=sport,
                week_starting=week_key,
                matches_count=data["matches"],
                hours_played=round(data["hours"], 1),
                total_revenue=round(data["revenue"], 2),
            )
        )

    return results


@router.get("/venues/{tenant_id}/peak-hours")
def get_venue_peak_hours(
    tenant_id: str,
    db: Client = Depends(get_db),
) -> dict[str, int]:
    """Identify peak booking hours at a venue (heatmap data for owners)."""
    bookings = booking_service.list_bookings(db, tenant_id)

    hour_counts = {}
    for booking in bookings:
        if booking.status != "confirmed":
            continue

        try:
            start_h = int(booking.start_time.split(":")[0])
            hour_counts[f"{start_h:02d}:00"] = hour_counts.get(f"{start_h:02d}:00", 0) + 1
        except (ValueError, IndexError):
            pass

    return hour_counts
