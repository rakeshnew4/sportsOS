from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.db.orm import User

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


def _build_profile(db: Session, uid: str, expose_phone: bool = False) -> PlayerProfile:
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        return PlayerProfile(uid=uid, display_name="Unknown", phone="", created_at="")

    engagement = kpi_service.get_player_engagement_kpi(db, uid, PlayerKPIScope.ALL_TIME)
    return PlayerProfile(
        uid=uid,
        display_name=user.display_name or "",
        phone=user.phone if expose_phone else "",
        total_bookings=engagement.courts_booked,
        total_matches_played=engagement.matches_played,
        total_hours_played=engagement.hours_played,
        favorite_sport=engagement.favorite_sport,
        repeat_venues_count=engagement.repeat_venues,
        avg_rating=None,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.get("/me/profile")
def get_my_profile(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlayerProfile:
    return _build_profile(db, user.uid, expose_phone=True)


@router.get("/{uid}/profile")
def get_player_profile(
    uid: str,
    db: Session = Depends(get_db),
) -> PlayerProfile:
    return _build_profile(db, uid, expose_phone=False)


@router.get("/search")
def search_players(
    sport: str | None = None,
    min_hours_played: float = 0.0,
    db: Session = Depends(get_db),
) -> PlayerSearchResult:
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    players = db.query(User).filter(User.is_player == True).all()
    results = []
    for u in players:
        engagement = kpi_service.get_player_engagement_kpi(db, u.uid, PlayerKPIScope.ALL_TIME)
        if sport and engagement.favorite_sport != sport.lower():
            continue
        if engagement.hours_played < min_hours_played:
            continue
        results.append(PlayerProfile(
            uid=u.uid, display_name=u.display_name or "", phone="",
            total_bookings=engagement.courts_booked,
            total_matches_played=engagement.matches_played,
            total_hours_played=engagement.hours_played,
            favorite_sport=engagement.favorite_sport,
            repeat_venues_count=engagement.repeat_venues,
            avg_rating=None,
            created_at=u.created_at.isoformat() if u.created_at else "",
        ))
    results.sort(key=lambda p: p.total_hours_played, reverse=True)
    return PlayerSearchResult(players=results, total=len(results))



