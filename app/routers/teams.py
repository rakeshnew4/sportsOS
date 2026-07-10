"""Team management and team-vs-team matchmaking."""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.db import Session, get_db
from app.core.security import CurrentUser, get_current_user
from app.db.orm import User
from app.models.team import TeamMember

router = APIRouter(prefix="/teams", tags=["teams"])


def _display_name(db: Session, uid: str) -> str:
    user = db.query(User).filter(User.uid == uid).first()
    return user.display_name if user and user.display_name else uid


class TeamResponse(BaseModel):
    team_id: str
    team_name: str
    sport: str
    captain_uid: str
    captain_name: str
    status: str
    members: list[TeamMember]
    total_members: int
    wins: int = 0
    losses: int = 0
    rating: float = 0.0
    created_at: str
    created_by: str
    booking_id: str | None = None


class TeamCreateRequest(BaseModel):
    team_name: str
    sport: str
    description: str | None = None


class TeamInviteRequest(BaseModel):
    player_uid: str
    player_name: str


class TeamOpponentRequest(BaseModel):
    sport: str
    date: str
    time: str
    venue_id: str | None = None
    skill_level: str | None = None
    match_format: str | None = None
    number_of_players: int = 11


class TeamOpponentResponse(BaseModel):
    challenge_id: str
    from_team_id: str
    from_team_name: str
    from_captain_uid: str
    from_captain_name: str
    sport: str
    date: str
    time: str
    venue_id: str | None = None
    skill_level: str | None = None
    match_format: str | None = None
    number_of_players: int
    status: str
    created_at: str


# Team Management

def _to_team_response(db: Session, team) -> "TeamResponse":
    stats = team.stats
    return TeamResponse(
        team_id=team.team_id,
        team_name=team.team_name,
        sport=team.sport,
        captain_uid=team.captain_uid,
        captain_name=_display_name(db, team.captain_uid),
        status=team.status,
        members=team.members,
        total_members=team.total_members,
        wins=stats.wins if stats else 0,
        losses=stats.losses if stats else 0,
        rating=stats.rating if stats else 0.0,
        created_at=team.created_at,
        created_by=team.captain_uid,
        booking_id=team.booking_id,
    )


@router.get("")
def list_teams(
    sport: str | None = None,
    db: Session = Depends(get_db),
) -> list[TeamResponse]:
    """List all active teams, optionally filtered by sport."""
    from app.services import team_service
    teams = team_service.list_teams(db, sport)
    return [_to_team_response(db, team) for team in teams]


@router.get("/me")
def list_my_teams(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TeamResponse]:
    """List teams the current player is in."""
    from app.services import team_service
    teams = team_service.list_player_teams(db, user.uid)
    return [_to_team_response(db, team) for team in teams]


@router.get("/available")
def discover_opponent_challenges(
    sport: str | None = None,
    date: str | None = None,
    db: Session = Depends(get_db),
) -> list[TeamOpponentResponse]:
    """Discover opponent challenges from other teams (for team discovery)."""
    from app.services import team_service
    challenges = team_service.discover_opponent_challenges(db, sport, date)
    return [TeamOpponentResponse(**c, from_captain_name=_display_name(db, c["from_captain_uid"])) for c in challenges]


@router.get("/{team_id}")
def get_team(
    team_id: str,
    db: Session = Depends(get_db),
) -> TeamResponse:
    """Get team details including members and stats."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return _to_team_response(db, team)


@router.post("", status_code=201)
def create_team(
    req: TeamCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamResponse:
    """Create a new team (user becomes captain)."""
    from app.services import team_service
    team = team_service.create_team(db, user.uid, req.sport, req.team_name)
    db.commit()
    return _to_team_response(db, team)


@router.patch("/{team_id}")
def update_team(
    team_id: str,
    req: TeamCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamResponse:
    """Update team info (captain only)."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team or team.captain_uid != user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only captain can update team")
    # TODO: implement team update in team_service
    raise HTTPException(status_code=501, detail="Not implemented")


# Team Members

@router.get("/{team_id}/members")
def list_team_members(
    team_id: str,
    db: Session = Depends(get_db),
) -> list[TeamMember]:
    """Get all members of a team."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team.members


@router.post("/{team_id}/members", status_code=201)
def invite_player_to_team(
    team_id: str,
    req: TeamInviteRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamMember:
    """Invite a player to join the team (captain only)."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team or team.captain_uid != user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only captain can invite players")
    updated_team = team_service.add_team_member(db, team_id, req.player_uid, req.player_name)
    db.commit()
    return next(m for m in updated_team.members if m.uid == req.player_uid)


@router.delete("/{team_id}/members/{player_uid}")
def remove_player_from_team(
    team_id: str,
    player_uid: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Remove a player from team (captain only or self-remove)."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.captain_uid != user.uid and player_uid != user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    team_service.remove_team_member(db, team_id, player_uid)
    db.commit()
    return {"success": True, "message": f"Player {player_uid} removed from team"}


# Team-vs-Team Challenges

@router.post("/{team_id}/challenges", status_code=201)
def create_opponent_challenge(
    team_id: str,
    req: TeamOpponentRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamOpponentResponse:
    """Create a 'looking for opponent' challenge (captain only)."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team or team.captain_uid != user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only captain can create challenges")

    challenge = team_service.create_opponent_challenge(
        db, team_id, user.uid, req.sport, req.date, req.time,
        req.venue_id, req.skill_level, req.match_format, req.number_of_players
    )
    db.commit()
    return TeamOpponentResponse(**challenge, from_captain_name=_display_name(db, challenge["from_captain_uid"]))


@router.get("/{team_id}/challenges")
def list_team_challenges(
    team_id: str,
    db: Session = Depends(get_db),
) -> list[TeamOpponentResponse]:
    """List opponent challenges from this team."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    challenges = team_service.list_team_challenges(db, team_id)
    return [TeamOpponentResponse(**c, from_captain_name=_display_name(db, c["from_captain_uid"])) for c in challenges]


@router.post("/{team_id}/challenges/{challenge_id}/accept", status_code=201)
def accept_opponent_challenge(
    team_id: str,
    challenge_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Accept an opponent challenge (creates match booking for both teams)."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team or team.captain_uid != user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only captain can accept challenges")

    result = team_service.accept_opponent_challenge(db, challenge_id, team_id, user.uid)
    db.commit()
    return {
        "success": True,
        "message": "Challenge accepted",
        "booking_id": result.get("booking_id"),
        "match_date": result.get("match_date"),
    }


@router.post("/{team_id}/challenges/{challenge_id}/reject")
def reject_opponent_challenge(
    team_id: str,
    challenge_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Reject an opponent challenge."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    team_service.reject_opponent_challenge(db, challenge_id)
    db.commit()
    return {"success": True, "message": "Challenge rejected"}


# Team Statistics & History (Phase 3)

@router.get("/{team_id}/stats")
def get_team_stats(
    team_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Get team statistics (wins, losses, rating)."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    stats = team_service.get_team_stats(db, team_id)
    return {
        "team_id": team_id,
        "team_name": team.team_name,
        "sport": team.sport,
        **stats
    }


@router.get("/{team_id}/history")
def get_team_history(
    team_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> dict:
    """Get team's match history (last N matches)."""
    from app.services import team_service
    team = team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    history = team_service.get_team_history(db, team_id, limit)
    return {
        "team_id": team_id,
        "team_name": team.team_name,
        "total_matches": len(history),
        "recent_matches": history
    }
