from fastapi import APIRouter, Depends, HTTPException, status as http_status
from pydantic import BaseModel

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.db.orm import Rating, User

router = APIRouter(prefix="/players", tags=["players"])

VALID_SKILL_LEVELS = ("beginner", "intermediate", "advanced", "pro")


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
    total_ratings: int = 0
    skill_levels: dict[str, str] = {}
    created_at: str


class SkillLevelsUpdate(BaseModel):
    skill_levels: dict[str, str]


class PlayerSearchResult(BaseModel):
    players: list[PlayerProfile]
    total: int


class InvitePreferences(BaseModel):
    open_to_invites: bool
    radius_km: float
    preferred_court_ids: list[str]


class InvitePreferencesUpdate(BaseModel):
    open_to_invites: bool | None = None
    radius_km: float | None = None
    preferred_court_ids: list[str] | None = None


def _build_profile(db: Session, uid: str, expose_phone: bool = False) -> PlayerProfile:
    from app.models.kpi import PlayerKPIScope
    from app.services import kpi_service

    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        return PlayerProfile(uid=uid, display_name="Unknown", phone="", created_at="")

    engagement = kpi_service.get_player_engagement_kpi(db, uid, PlayerKPIScope.ALL_TIME)
    ratings = db.query(Rating).filter(Rating.to_uid == uid).all()
    avg_rating = round(sum(r.rating for r in ratings) / len(ratings), 2) if ratings else None
    return PlayerProfile(
        uid=uid,
        display_name=user.display_name or "",
        phone=user.phone if expose_phone else "",
        total_bookings=engagement.courts_booked,
        total_matches_played=engagement.matches_played,
        total_hours_played=engagement.hours_played,
        favorite_sport=engagement.favorite_sport,
        repeat_venues_count=engagement.repeat_venues,
        avg_rating=avg_rating,
        total_ratings=len(ratings),
        skill_levels=user.skill_levels or {},
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


@router.put("/me/skills")
def update_my_skills(
    req: SkillLevelsUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlayerProfile:
    for sport, level in req.skill_levels.items():
        if level not in VALID_SKILL_LEVELS:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid skill level '{level}' for {sport}. Must be one of {VALID_SKILL_LEVELS}.",
            )

    db_user = db.query(User).filter(User.uid == user.uid).first()
    if not db_user:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    db_user.skill_levels = {**(db_user.skill_levels or {}), **req.skill_levels}
    db.commit()
    return _build_profile(db, user.uid, expose_phone=True)


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


@router.get("/me/invite-preferences")
def get_invite_preferences(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvitePreferences:
    """Whether this player is open to receiving match invites from players they haven't played with, and within what radius/courts."""
    from app.services import invite_service
    pref = invite_service.get_invite_preferences(db, user.uid)
    return InvitePreferences(
        open_to_invites=pref.open_to_invites, radius_km=pref.radius_km, preferred_court_ids=pref.preferred_court_ids,
    )


@router.put("/me/invite-preferences")
def update_invite_preferences(
    req: InvitePreferencesUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvitePreferences:
    from app.services import invite_service
    pref = invite_service.update_invite_preferences(
        db, user.uid,
        open_to_invites=req.open_to_invites, radius_km=req.radius_km, preferred_court_ids=req.preferred_court_ids,
    )
    return InvitePreferences(
        open_to_invites=pref.open_to_invites, radius_km=pref.radius_km, preferred_court_ids=pref.preferred_court_ids,
    )



