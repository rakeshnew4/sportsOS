from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Team, TeamMember, TeamMatchHistory, TeamStats, TeamChallenge
from app.models.team import TeamCreateRequest, TeamResponse, TeamMember as TeamMemberModel


def get_team(db: Session, team_id: str) -> TeamResponse:
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return _to_response(team)


def _to_response(team: Team) -> TeamResponse:
    from app.models.team import TeamStats as TeamStatsModel
    members = [
        TeamMemberModel(uid=m.uid, display_name=m.display_name, joined_at=m.joined_at.isoformat())
        for m in team.members
    ]
    stats = None
    if team.stats:
        s = team.stats
        stats = TeamStatsModel(
            total_matches=s.total_matches,
            wins=s.wins,
            losses=s.losses,
            draws=s.draws,
            win_rate=s.win_rate,
            rating=s.rating,
            last_match_at=s.last_match_at,
        )
    return TeamResponse(
        team_id=team.team_id,
        team_name=team.team_name,
        sport=team.sport,
        captain_uid=team.captain_uid,
        status=team.status,
        members=members,
        total_members=len(members),
        booking_id=team.booking_id,
        created_at=team.created_at.isoformat(),
        created_by=team.created_by,
        stats=stats,
    )


def create_team(db: Session, captain_uid: str, sport: str, team_name: str | None = None) -> TeamResponse:
    team_id = str(uuid.uuid4())
    if not team_name:
        team_name = f"{sport.title()} Team {team_id[:8]}"
    now = datetime.now(timezone.utc)
    team = Team(
        team_id=team_id,
        team_name=team_name,
        sport=sport,
        captain_uid=captain_uid,
        status="forming",
        booking_id=None,
        created_at=now,
        created_by=captain_uid,
    )
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team_id, uid=captain_uid, display_name=None, joined_at=now))
    db.add(TeamStats(team_id=team_id))
    db.flush()
    db.refresh(team)
    return _to_response(team)


def add_team_member(db: Session, team_id: str, uid: str, display_name: str | None = None) -> TeamResponse:
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    existing = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.uid == uid).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member of this team")
    db.add(TeamMember(team_id=team_id, uid=uid, display_name=display_name, joined_at=datetime.now(timezone.utc)))
    db.flush()
    db.refresh(team)
    return _to_response(team)


def get_team_members(db: Session, team_id: str) -> list[TeamMemberModel]:
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    return [TeamMemberModel(uid=m.uid, display_name=m.display_name, joined_at=m.joined_at.isoformat()) for m in members]


def link_booking_to_team(db: Session, team_id: str, booking_id: str, team_status: str = "active") -> TeamResponse:
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    team.booking_id = booking_id
    team.status = team_status
    db.flush()
    db.refresh(team)
    return _to_response(team)


def remove_team_member(db: Session, team_id: str, uid: str) -> TeamResponse:
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.captain_uid == uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captain cannot leave the team")
    member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.uid == uid).first()
    if member:
        db.delete(member)
        db.flush()
    db.refresh(team)
    return _to_response(team)


def list_teams(db: Session, sport: str | None = None) -> list[TeamResponse]:
    query = db.query(Team).filter(Team.status == "active")
    if sport:
        query = query.filter(Team.sport == sport)
    return [_to_response(t) for t in query.all()]


def list_player_teams(db: Session, player_uid: str) -> list[TeamResponse]:
    memberships = db.query(TeamMember).filter(TeamMember.uid == player_uid).all()
    team_ids = [m.team_id for m in memberships]
    teams = db.query(Team).filter(Team.team_id.in_(team_ids)).all()
    return [_to_response(t) for t in teams]


def create_opponent_challenge(
    db: Session, team_id: str, captain_uid: str, sport: str, date: str, time: str,
    venue_id: str | None = None, skill_level: str | None = None,
    match_format: str | None = None, number_of_players: int = 11,
) -> dict:
    team = get_team(db, team_id)
    challenge_id = str(uuid.uuid4())
    challenge = TeamChallenge(
        id=challenge_id,
        from_captain_uid=captain_uid,
        to_captain_uid=captain_uid,  # placeholder until accepted
        booking_id=None,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(challenge)
    db.flush()
    return {
        "challenge_id": challenge_id,
        "from_team_id": team_id,
        "from_team_name": team.team_name,
        "from_captain_uid": captain_uid,
        "sport": sport,
        "date": date,
        "time": time,
        "venue_id": venue_id,
        "skill_level": skill_level,
        "match_format": match_format,
        "number_of_players": number_of_players,
        "status": "pending",
        "created_at": challenge.created_at.isoformat(),
    }


def list_team_challenges(db: Session, captain_uid: str) -> list[dict]:
    challenges = db.query(TeamChallenge).filter(TeamChallenge.from_captain_uid == captain_uid).all()
    return [{"id": c.id, "status": c.status, "created_at": c.created_at.isoformat()} for c in challenges]


def discover_opponent_challenges(db: Session, sport: str | None = None, date: str | None = None) -> list[dict]:
    challenges = db.query(TeamChallenge).filter(TeamChallenge.status == "pending").all()
    return [{"id": c.id, "from_captain_uid": c.from_captain_uid, "status": c.status} for c in challenges]


def accept_opponent_challenge(db: Session, challenge_id: str, accepting_team_id: str, accepting_captain_uid: str) -> dict:
    challenge = db.query(TeamChallenge).filter(TeamChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    challenge.status = "accepted"
    challenge.to_captain_uid = accepting_captain_uid
    db.flush()
    return {
        "challenge_id": challenge_id,
        "status": "accepted",
        "message": "Challenge accepted! Both captains will receive credits when match completes.",
    }


def reject_opponent_challenge(db: Session, challenge_id: str) -> dict:
    challenge = db.query(TeamChallenge).filter(TeamChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    challenge.status = "rejected"
    db.flush()
    return {"status": "rejected", "message": "Challenge rejected"}


def record_team_match(
    db: Session, team_id: str, booking_id: str, opponent_team_id: str,
    opponent_team_name: str, result: str, player_count: int, venue_id: str | None = None,
) -> dict:
    match_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    history = TeamMatchHistory(
        team_id=team_id,
        match_id=match_id,
        booking_id=booking_id,
        opponent_team_id=opponent_team_id,
        opponent_team_name=opponent_team_name,
        result=result,
        player_count=player_count,
        played_at=now,
        venue_id=venue_id,
    )
    db.add(history)

    stats = db.query(TeamStats).filter(TeamStats.team_id == team_id).first()
    if stats:
        stats.total_matches += 1
        if result == "win":
            stats.wins += 1
            stats.rating += 25.0
        elif result == "loss":
            stats.losses += 1
            stats.rating -= 20.0
        else:
            stats.draws += 1
        stats.win_rate = (stats.wins / stats.total_matches * 100) if stats.total_matches > 0 else 0.0
        stats.last_match_at = now
    db.flush()
    return {"match_id": match_id, "result": result, "played_at": now}


def get_team_history(db: Session, team_id: str, limit: int = 10) -> list[dict]:
    history = (
        db.query(TeamMatchHistory)
        .filter(TeamMatchHistory.team_id == team_id)
        .order_by(TeamMatchHistory.played_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "match_id": h.match_id,
            "booking_id": h.booking_id,
            "opponent_team_id": h.opponent_team_id,
            "opponent_team_name": h.opponent_team_name,
            "result": h.result,
            "player_count": h.player_count,
            "played_at": h.played_at,
            "venue_id": h.venue_id,
        }
        for h in history
    ]


def get_team_stats(db: Session, team_id: str) -> dict:
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    s = db.query(TeamStats).filter(TeamStats.team_id == team_id).first()
    if not s:
        return {"total_matches": 0, "wins": 0, "losses": 0, "draws": 0, "win_rate": 0.0, "rating": 1200.0, "last_match_at": None}
    return {
        "total_matches": s.total_matches,
        "wins": s.wins,
        "losses": s.losses,
        "draws": s.draws,
        "win_rate": s.win_rate,
        "rating": s.rating,
        "last_match_at": s.last_match_at,
    }
