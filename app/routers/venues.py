from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Client, FieldFilter, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.venue import VenueCreateRequest, VenueResponse
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
    db: Client = Depends(get_db),
) -> VenueResponse:
    return venue_service.create_venue(db, user.uid, req)


@router.get("/{tenant_id}")
def get_venue(
    tenant_id: str,
    db: Client = Depends(get_db),
) -> VenueResponse:
    return venue_service.get_venue(db, tenant_id)


@router.get("/{tenant_id}/players")
def list_venue_players(
    tenant_id: str,
    sort: str = "bookings",  # bookings, spend, recent
    db: Client = Depends(get_db),
) -> VenuePlayersResponse:
    """Get roster of players who've booked at this venue, sorted by engagement metric."""
    # Collect all unique players who have bookings at this venue
    player_stats: dict[str, dict] = {}

    bookings = booking_service.list_bookings(db, tenant_id)
    for booking in bookings:
        if booking.status != "confirmed":
            continue

        # Captain who created the booking
        captain_id = booking.created_by
        if captain_id not in player_stats:
            player_stats[captain_id] = {
                "uid": captain_id,
                "bookings": 0,
                "spend": 0.0,
                "sports": {},
                "last_booking": None,
            }
        player_stats[captain_id]["bookings"] += 1
        player_stats[captain_id]["spend"] += booking.price
        player_stats[captain_id]["sports"][booking.sport] = player_stats[captain_id]["sports"].get(booking.sport, 0) + 1
        player_stats[captain_id]["last_booking"] = booking.date

        # Participants who joined
        participant_docs = list(
            db.collection("tenants").document(tenant_id)
            .collection("bookings").document(booking.booking_id)
            .collection("participants").stream()
        )
        for participant_doc in participant_docs:
            participant_uid = participant_doc.id
            if participant_uid == captain_id:
                continue  # Already counted above
            if participant_uid not in player_stats:
                player_stats[participant_uid] = {
                    "uid": participant_uid,
                    "bookings": 0,
                    "spend": 0.0,
                    "sports": {},
                    "last_booking": None,
                }
            player_stats[participant_uid]["bookings"] += 1
            player_stats[participant_uid]["spend"] += booking.price / len(participant_docs)
            player_stats[participant_uid]["sports"][booking.sport] = (
                player_stats[participant_uid]["sports"].get(booking.sport, 0) + 1
            )
            player_stats[participant_uid]["last_booking"] = booking.date

    # Fetch user display names
    results = []
    for uid, stats in player_stats.items():
        user_doc = db.collection("users").document(uid).get()
        display_name = user_doc.to_dict().get("display_name", uid) if user_doc.exists else uid

        results.append(
            VenuePlayerStats(
                uid=uid,
                display_name=display_name,
                total_bookings=stats["bookings"],
                total_spend=round(stats["spend"], 2),
                favorite_sport=max(stats["sports"], key=stats["sports"].get) if stats["sports"] else None,
                last_booking=stats["last_booking"],
            )
        )

    # Sort
    if sort == "spend":
        results.sort(key=lambda p: p.total_spend, reverse=True)
    elif sort == "recent":
        results.sort(key=lambda p: p.last_booking or "", reverse=True)
    else:  # default: bookings
        results.sort(key=lambda p: p.total_bookings, reverse=True)

    return VenuePlayersResponse(venue_id=tenant_id, players=results, total=len(results))


@router.get("/{tenant_id}/analytics/revenue")
def venue_revenue_analytics(
    tenant_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    db: Client = Depends(get_db),
) -> RevenueAnalyticsResponse:
    """Get daily revenue breakdown for a venue over a date range."""
    from datetime import datetime, timedelta

    # Parse dates or default to last 30 days
    if to_date:
        end = datetime.fromisoformat(to_date)
    else:
        end = datetime.now()

    if from_date:
        start = datetime.fromisoformat(from_date)
    else:
        start = end - timedelta(days=30)

    # Collect bookings in date range
    bookings = booking_service.list_bookings(db, tenant_id)

    daily_revenue: dict[str, dict] = {}
    for booking in bookings:
        if booking.status != "confirmed":
            continue

        booking_date = booking.date
        try:
            bdate = datetime.fromisoformat(booking_date)
            if not (start <= bdate <= end):
                continue
        except (ValueError, TypeError):
            continue

        if booking_date not in daily_revenue:
            daily_revenue[booking_date] = {"revenue": 0.0, "bookings": 0, "prices": []}

        daily_revenue[booking_date]["revenue"] += booking.price
        daily_revenue[booking_date]["bookings"] += 1
        daily_revenue[booking_date]["prices"].append(booking.price)

    # Convert to response format
    daily_data = []
    total_revenue = 0.0
    total_bookings = 0

    for date_str in sorted(daily_revenue.keys()):
        data = daily_revenue[date_str]
        avg_price = sum(data["prices"]) / len(data["prices"]) if data["prices"] else 0.0
        daily_data.append(
            DailyRevenue(
                date=date_str,
                revenue=round(data["revenue"], 2),
                bookings_count=data["bookings"],
                avg_price=round(avg_price, 2),
            )
        )
        total_revenue += data["revenue"]
        total_bookings += data["bookings"]

    return RevenueAnalyticsResponse(
        venue_id=tenant_id,
        daily_data=daily_data,
        total_revenue=round(total_revenue, 2),
        total_bookings=total_bookings,
        date_range=f"{start.date()} to {end.date()}",
    )
