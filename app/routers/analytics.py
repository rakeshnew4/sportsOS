from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.db.orm import BookingParticipant, Tenant
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
    db: Session = Depends(get_db),
) -> list[MatchHistory]:
    my_bookings = booking_service.list_my_bookings(db, user.uid)
    results = []
    for booking in my_bookings:
        if booking.status != "confirmed":
            continue
        tenant = db.query(Tenant).filter(Tenant.tenant_id == booking.tenant_id).first()
        venue_name = tenant.name if tenant else booking.tenant_id
        participant_count = 1 + db.query(BookingParticipant).filter(
            BookingParticipant.booking_id == booking.booking_id
        ).count()
        price_per_person = booking.price / participant_count
        results.append(MatchHistory(
            booking_id=booking.booking_id, date=booking.date, sport=booking.sport,
            start_time=booking.start_time, end_time=booking.end_time,
            venue_name=venue_name, participants_count=participant_count,
            price_paid=round(price_per_person, 2), status=booking.status,
        ))
    results.sort(key=lambda m: m.date, reverse=True)
    return results[:limit]


@router.get("/players/me/stats")
def get_my_match_stats(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchStats:
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    all_time = kpi_service.get_player_engagement_kpi(db, user.uid, PlayerKPIScope.ALL_TIME)
    month = kpi_service.get_player_engagement_kpi(db, user.uid, PlayerKPIScope.MONTH)
    week = kpi_service.get_player_engagement_kpi(db, user.uid, PlayerKPIScope.QUARTER)
    my_bookings = booking_service.list_my_bookings(db, user.uid)
    confirmed = [b for b in my_bookings if b.status == "confirmed"]

    day_counts: dict[str, int] = {}
    for b in confirmed:
        try:
            bdate = datetime.fromisoformat(b.date)
            day = bdate.strftime("%A")
            day_counts[day] = day_counts.get(day, 0) + 1
        except (ValueError, TypeError):
            pass
    favorite_day = max(day_counts, key=lambda d: day_counts[d]) if day_counts else None

    avg_participants = 0.0
    if confirmed:
        total = sum(
            1 + db.query(BookingParticipant).filter(BookingParticipant.booking_id == b.booking_id).count()
            for b in confirmed
        )
        avg_participants = total / len(confirmed)

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
    db: Session = Depends(get_db),
) -> list[SportActivityTrend]:
    bookings = booking_service.list_bookings(db, tenant_id)
    now = datetime.now()
    trends: dict[tuple[str, str], dict] = {}
    for b in bookings:
        if b.status != "confirmed":
            continue
        try:
            bdate = datetime.fromisoformat(b.date)
        except (ValueError, TypeError):
            continue
        if (now - bdate).days > weeks * 7:
            continue
        week_start = (bdate - timedelta(days=bdate.weekday())).date().isoformat()
        key = (week_start, b.sport)
        if key not in trends:
            trends[key] = {"matches": 0, "hours": 0.0, "revenue": 0.0}
        trends[key]["matches"] += 1
        try:
            sh, sm = map(int, b.start_time.split(":"))
            eh, em = map(int, b.end_time.split(":"))
            trends[key]["hours"] += (eh + em / 60) - (sh + sm / 60)
        except (ValueError, AttributeError):
            pass
        trends[key]["revenue"] += b.price
    return [
        SportActivityTrend(sport=sport, week_starting=week, matches_count=d["matches"],
                           hours_played=round(d["hours"], 1), total_revenue=round(d["revenue"], 2))
        for (week, sport), d in sorted(trends.items())
    ]


@router.get("/venues/{tenant_id}/peak-hours")
def get_venue_peak_hours(
    tenant_id: str,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    bookings = booking_service.list_bookings(db, tenant_id)
    hour_counts: dict[str, int] = {}
    for b in bookings:
        if b.status != "confirmed":
            continue
        try:
            start_h = int(b.start_time.split(":")[0])
            hour_counts[f"{start_h:02d}:00"] = hour_counts.get(f"{start_h:02d}:00", 0) + 1
        except (ValueError, IndexError):
            pass
    return hour_counts


