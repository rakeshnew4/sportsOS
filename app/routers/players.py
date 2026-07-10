from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Client, FieldFilter, get_db
from app.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/players", tags=["players"])


class PlayerProfile(BaseModel):
    uid: str
    display_name: str
    phone: str
    total_bookings: int = 0
    total_matches_played: int = 0
    total_hours_played: float = 0.0
    favorite_sport: str | None = None
    repeat_venues_count: int = 0
    avg_rating: float | None = None
    created_at: str


class PlayerSearchResult(BaseModel):
    players: list[PlayerProfile]
    total: int


@router.get("/me/profile")
def get_my_profile(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> PlayerProfile:
    """Get current player's profile with stats."""
    user_doc = db.collection("users").document(user.uid).get()
    if not user_doc.exists:
        return PlayerProfile(uid=user.uid, display_name="Unknown", phone="", created_at="")

    user_data = user_doc.to_dict()

    # Get player engagement KPI to populate stats
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    engagement = kpi_service.get_player_engagement_kpi(db, user.uid, PlayerKPIScope.ALL_TIME)

    return PlayerProfile(
        uid=user.uid,
        display_name=user_data.get("display_name", ""),
        phone=user_data.get("phone", ""),
        total_bookings=engagement.courts_booked,
        total_matches_played=engagement.matches_played,
        total_hours_played=engagement.hours_played,
        favorite_sport=engagement.favorite_sport,
        repeat_venues_count=engagement.repeat_venues,
        avg_rating=None,  # TODO: implement ratings
        created_at=user_data.get("created_at", ""),
    )


@router.get("/{uid}/profile")
def get_player_profile(
    uid: str,
    db: Client = Depends(get_db),
) -> PlayerProfile:
    """Get a player's public profile."""
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        return PlayerProfile(uid=uid, display_name="Unknown", phone="", created_at="")

    user_data = user_doc.to_dict()

    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    engagement = kpi_service.get_player_engagement_kpi(db, uid, PlayerKPIScope.ALL_TIME)

    return PlayerProfile(
        uid=uid,
        display_name=user_data.get("display_name", ""),
        phone="",  # Don't expose phone publicly
        total_bookings=engagement.courts_booked,
        total_matches_played=engagement.matches_played,
        total_hours_played=engagement.hours_played,
        favorite_sport=engagement.favorite_sport,
        repeat_venues_count=engagement.repeat_venues,
        avg_rating=None,
        created_at=user_data.get("created_at", ""),
    )


@router.get("/search")
def search_players(
    sport: str | None = None,
    min_hours_played: float = 0.0,
    db: Client = Depends(get_db),
) -> PlayerSearchResult:
    """Search for players by sport or experience level. Useful for matchmaking."""
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    # Get all players
    users = []
    for doc in db.collection("users").where(filter=FieldFilter("roles.player", "==", True)).stream():
        user_data = doc.to_dict()
        users.append({"uid": doc.id, **user_data})

    # Enrich with stats
    results = []
    for user in users:
        engagement = kpi_service.get_player_engagement_kpi(db, user["uid"], PlayerKPIScope.ALL_TIME)

        # Filter by sport if specified
        if sport and engagement.favorite_sport != sport.lower():
            continue

        # Filter by hours played
        if engagement.hours_played < min_hours_played:
            continue

        results.append(
            PlayerProfile(
                uid=user["uid"],
                display_name=user.get("display_name", ""),
                phone="",
                total_bookings=engagement.courts_booked,
                total_matches_played=engagement.matches_played,
                total_hours_played=engagement.hours_played,
                favorite_sport=engagement.favorite_sport,
                repeat_venues_count=engagement.repeat_venues,
                avg_rating=None,
                created_at=user.get("created_at", ""),
            )
        )

    # Sort by hours played (most experienced first)
    results.sort(key=lambda p: p.total_hours_played, reverse=True)

    return PlayerSearchResult(players=results, total=len(results))
