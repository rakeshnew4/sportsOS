from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user, require_venue_access
from app.db.orm import BookingParticipant, User
from app.models.venue import VenueCreateRequest, VenueResponse, VenueUpdateRequest
from app.services import booking_service, venue_service

router = APIRouter(prefix="/venues", tags=["venues"])


class DailyRevenue(BaseModel):
    date: str
    revenue: float
    bookings_count: int
    avg_price: float = 0.0
    occupancy_percent: float = 0.0


class RevenueAnalyticsResponse(BaseModel):
    venue_id: str
    daily_data: list[DailyRevenue]
    total_revenue: float = 0.0
    total_bookings: int = 0
    date_range: str = ""


class VenuePlayerStats(BaseModel):
    uid: str
    display_name: str
    total_bookings: int
    total_spend: float = 0.0
    favorite_sport: str | None = None
    last_booking: str | None = None


class VenuePlayersResponse(BaseModel):
    venue_id: str
    players: list[VenuePlayerStats]
    total: int


@router.post("", status_code=201)
def create_venue(
    req: VenueCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VenueResponse:
    return venue_service.create_venue(db, user.uid, req)


@router.get("")
def list_venues(
    city: str | None = None,
    sport: str | None = None,
    db: Session = Depends(get_db),
) -> list[VenueResponse]:
    return venue_service.list_venues(db, city, sport)


@router.get("/{tenant_id}")
def get_venue(
    tenant_id: str,
    db: Session = Depends(get_db),
) -> VenueResponse:
    return venue_service.get_venue(db, tenant_id)


@router.patch("/{tenant_id}")
def update_venue(
    tenant_id: str,
    req: VenueUpdateRequest,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> VenueResponse:
    return venue_service.update_venue(db, tenant_id, req)


@router.get("/{tenant_id}/players")
def list_venue_players(
    tenant_id: str,
    sort: str = "bookings",
    db: Session = Depends(get_db),
) -> VenuePlayersResponse:
    player_stats: dict[str, dict] = {}
    bookings = booking_service.list_bookings(db, tenant_id)
    for b in bookings:
        if b.status != "confirmed":
            continue
        for uid in [b.created_by] + [
            p.uid for p in db.query(BookingParticipant).filter(BookingParticipant.booking_id == b.booking_id).all()
        ]:
            if uid not in player_stats:
                player_stats[uid] = {"bookings": 0, "spend": 0.0, "sports": {}, "last_booking": None}
            player_stats[uid]["bookings"] += 1
            player_stats[uid]["spend"] += b.price
            player_stats[uid]["sports"][b.sport] = player_stats[uid]["sports"].get(b.sport, 0) + 1
            player_stats[uid]["last_booking"] = b.date

    results = []
    for uid, stats in player_stats.items():
        user = db.query(User).filter(User.uid == uid).first()
        display_name = user.display_name if user else uid
        results.append(VenuePlayerStats(
            uid=uid, display_name=display_name,
            total_bookings=stats["bookings"], total_spend=round(stats["spend"], 2),
            favorite_sport=max(stats["sports"], key=stats["sports"].get) if stats["sports"] else None,
            last_booking=stats["last_booking"],
        ))
    if sort == "spend":
        results.sort(key=lambda p: p.total_spend, reverse=True)
    elif sort == "recent":
        results.sort(key=lambda p: p.last_booking or "", reverse=True)
    else:
        results.sort(key=lambda p: p.total_bookings, reverse=True)
    return VenuePlayersResponse(venue_id=tenant_id, players=results, total=len(results))


@router.get("/{tenant_id}/analytics/revenue")
def venue_revenue_analytics(
    tenant_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    db: Session = Depends(get_db),
) -> RevenueAnalyticsResponse:
    end = datetime.fromisoformat(to_date) if to_date else datetime.now()
    start = datetime.fromisoformat(from_date) if from_date else (end - timedelta(days=30))
    bookings = booking_service.list_bookings(db, tenant_id)
    daily: dict[str, dict] = {}
    for b in bookings:
        if b.status != "confirmed":
            continue
        try:
            bdate = datetime.fromisoformat(b.date)
            if not (start <= bdate <= end):
                continue
        except (ValueError, TypeError):
            continue
        if b.date not in daily:
            daily[b.date] = {"revenue": 0.0, "bookings": 0, "prices": []}
        daily[b.date]["revenue"] += b.price
        daily[b.date]["bookings"] += 1
        daily[b.date]["prices"].append(b.price)

    daily_data = []
    total_revenue = 0.0
    total_bookings = 0
    for date_str in sorted(daily):
        d = daily[date_str]
        avg_price = sum(d["prices"]) / len(d["prices"]) if d["prices"] else 0.0
        daily_data.append(DailyRevenue(
            date=date_str, revenue=round(d["revenue"], 2),
            bookings_count=d["bookings"], avg_price=round(avg_price, 2),
        ))
        total_revenue += d["revenue"]
        total_bookings += d["bookings"]
    return RevenueAnalyticsResponse(
        venue_id=tenant_id, daily_data=daily_data,
        total_revenue=round(total_revenue, 2), total_bookings=total_bookings,
        date_range=f"{start.date()} to {end.date()}",
    )


class BroadcastNotificationRequest(BaseModel):
    title: str
    body: str


class BroadcastNotificationResponse(BaseModel):
    recipient_count: int


@router.post("/{tenant_id}/notifications/broadcast")
def broadcast_notification(
    tenant_id: str,
    req: BroadcastNotificationRequest,
    user: CurrentUser = Depends(require_venue_access),
    db: Session = Depends(get_db),
) -> BroadcastNotificationResponse:
    """Venue owner/staff send an announcement to everyone who's booked at this venue."""
    from app.services import notification_service

    venue = venue_service.get_venue(db, tenant_id)
    player_uids = booking_service.get_venue_player_uids(db, tenant_id)
    count = notification_service.notify_venue_announcement(db, tenant_id, player_uids, venue.name, req.title, req.body)
    return BroadcastNotificationResponse(recipient_count=count)



