from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status

from app.core.db import Client, FieldFilter
from app.models.team import TeamCreateRequest, TeamResponse, TeamMember


def teams_collection(db: Client):
    return db.collection("teams")


def team_members_ref(db: Client, team_id: str):
    return db.collection("teams").document(team_id).collection("members")


def get_team(db: Client, team_id: str) -> TeamResponse:
    doc = teams_collection(db).document(team_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    data = doc.to_dict()
    members = []
    for member_doc in team_members_ref(db, team_id).stream():
        member_data = member_doc.to_dict()
        members.append(TeamMember(uid=member_doc.id, display_name=member_data.get("display_name"), joined_at=member_data["joined_at"]))
    return TeamResponse(
        team_id=team_id,
        team_name=data["team_name"],
        sport=data["sport"],
        status=data.get("status", "forming"),
        captain_uid=data["captain_uid"],
        members=members,
        total_members=len(members),
        booking_id=data.get("booking_id"),
        created_at=data["created_at"],
    )


def create_team(db: Client, captain_uid: str, sport: str, team_name: str | None = None) -> TeamResponse:
    team_id = str(uuid.uuid4())
    if not team_name:
        team_name = f"{sport.title()} Team {team_id[:8]}"

    now = datetime.now(timezone.utc).isoformat()
    team_data = {
        "team_name": team_name,
        "sport": sport,
        "captain_uid": captain_uid,
        "status": "forming",
        "booking_id": None,
        "created_at": now,
    }
    teams_collection(db).document(team_id).set(team_data)

    # Add captain as first member
    team_members_ref(db, team_id).document(captain_uid).set({
        "display_name": None,
        "joined_at": now,
    })

    return TeamResponse(
        team_id=team_id,
        team_name=team_name,
        sport=sport,
        status="forming",
        captain_uid=captain_uid,
        members=[TeamMember(uid=captain_uid, display_name=None, joined_at=now)],
        total_members=1,
        booking_id=None,
        created_at=now,
    )


def add_team_member(db: Client, team_id: str, uid: str, display_name: str | None = None) -> TeamResponse:
    team_doc = teams_collection(db).document(team_id).get()
    if not team_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    team_data = team_doc.to_dict()

    # Check if already a member
    member_doc = team_members_ref(db, team_id).document(uid).get()
    if member_doc.exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member of this team")

    now = datetime.now(timezone.utc).isoformat()
    team_members_ref(db, team_id).document(uid).set({
        "display_name": display_name,
        "joined_at": now,
    })

    return get_team(db, team_id)


def get_team_members(db: Client, team_id: str) -> list[TeamMember]:
    members = []
    for doc in team_members_ref(db, team_id).stream():
        data = doc.to_dict()
        members.append(TeamMember(uid=doc.id, display_name=data.get("display_name"), joined_at=data["joined_at"]))
    return members


def link_booking_to_team(db: Client, team_id: str, booking_id: str, status: str = "active") -> TeamResponse:
    teams_collection(db).document(team_id).update({
        "booking_id": booking_id,
        "status": status,
    })
    return get_team(db, team_id)


def remove_team_member(db: Client, team_id: str, uid: str) -> TeamResponse:
    team_doc = teams_collection(db).document(team_id).get()
    if not team_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    team_data = team_doc.to_dict()
    if team_data["captain_uid"] == uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captain cannot leave the team")

    team_members_ref(db, team_id).document(uid).delete()
    return get_team(db, team_id)


def list_teams(db: Client, sport: str | None = None) -> list[TeamResponse]:
    """List all active teams, optionally filtered by sport."""
    query = db.collection("teams").where(filter=FieldFilter("status", "==", "active"))
    if sport:
        query = query.where(filter=FieldFilter("sport", "==", sport))

    teams = []
    for doc in query.stream():
        teams.append(get_team(db, doc.id))
    return teams


def list_player_teams(db: Client, player_uid: str) -> list[TeamResponse]:
    """List all teams a player is member of."""
    # Query teams where player is a member
    teams = []
    for team_doc in db.collection("teams").stream():
        team_id = team_doc.id
        if team_members_ref(db, team_id).document(player_uid).get().exists:
            teams.append(get_team(db, team_id))
    return teams


def create_opponent_challenge(
    db: Client, team_id: str, captain_uid: str, sport: str, date: str, time: str,
    venue_id: str | None = None, skill_level: str | None = None,
    match_format: str | None = None, number_of_players: int = 11
) -> dict:
    """Create a 'looking for opponent' challenge."""
    challenge_id = str(uuid.uuid4())
    team = get_team(db, team_id)

    challenge_data = {
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection("team_challenges").document(challenge_id).set(challenge_data)
    return challenge_data


def list_team_challenges(db: Client, team_id: str) -> list[dict]:
    """List challenges created by a team."""
    challenges = []
    for doc in db.collection("team_challenges").where(filter=FieldFilter("from_team_id", "==", team_id)).stream():
        challenges.append(doc.to_dict())
    return challenges


def discover_opponent_challenges(db: Client, sport: str | None = None, date: str | None = None) -> list[dict]:
    """Discover available opponent challenges (for team discovery)."""
    query = db.collection("team_challenges").where(filter=FieldFilter("status", "==", "pending"))
    if sport:
        query = query.where(filter=FieldFilter("sport", "==", sport))
    if date:
        query = query.where(filter=FieldFilter("date", "==", date))

    challenges = []
    for doc in query.stream():
        challenges.append(doc.to_dict())
    return challenges


def accept_opponent_challenge(db: Client, challenge_id: str, accepting_team_id: str, accepting_captain_uid: str) -> dict:
    """Accept an opponent challenge (creates booking for both teams)."""
    challenge_doc = db.collection("team_challenges").document(challenge_id).get()
    if not challenge_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    challenge = challenge_doc.to_dict()
    from_team = get_team(db, challenge["from_team_id"])

    # Mark challenge as accepted
    db.collection("team_challenges").document(challenge_id).update({
        "status": "accepted",
        "accepted_by_team_id": accepting_team_id,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
    })

    # TODO: Create booking for both teams (implement in booking_service.create_team_vs_team_booking)

    return {
        "challenge_id": challenge_id,
        "status": "accepted",
        "from_team": from_team.team_name,
        "accepting_team": get_team(db, accepting_team_id).team_name,
        "message": "Challenge accepted! Both captains will receive credits when match completes.",
    }


def reject_opponent_challenge(db: Client, challenge_id: str) -> dict:
    """Reject an opponent challenge."""
    db.collection("team_challenges").document(challenge_id).update({
        "status": "rejected",
        "rejected_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "rejected", "message": "Challenge rejected"}


# Team History & Stats

def record_team_match(
    db: Client, team_id: str, booking_id: str, opponent_team_id: str,
    opponent_team_name: str, result: str, player_count: int, venue_id: str | None = None
) -> dict:
    """Record a match result in team history."""
    match_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    match_data = {
        "match_id": match_id,
        "booking_id": booking_id,
        "opponent_team_id": opponent_team_id,
        "opponent_team_name": opponent_team_name,
        "result": result,  # win, loss, draw
        "player_count": player_count,
        "played_at": now,
        "venue_id": venue_id,
    }

    # Add to team's match history
    db.collection("teams").document(team_id).collection("history").document(match_id).set(match_data)

    # Update team stats
    team_doc = teams_collection(db).document(team_id).get()
    if team_doc.exists:
        team_data = team_doc.to_dict()
        stats = team_data.get("stats", {})

        total_matches = stats.get("total_matches", 0) + 1
        wins = stats.get("wins", 0) + (1 if result == "win" else 0)
        losses = stats.get("losses", 0) + (1 if result == "loss" else 0)
        draws = stats.get("draws", 0) + (1 if result == "draw" else 0)
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0.0

        # ELO rating update (simplified)
        rating = stats.get("rating", 1200.0)
        if result == "win":
            rating += 25.0
        elif result == "loss":
            rating -= 20.0

        new_stats = {
            "total_matches": total_matches,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": win_rate,
            "rating": rating,
            "last_match_at": now,
        }

        teams_collection(db).document(team_id).update({"stats": new_stats})

    return match_data


def get_team_history(db: Client, team_id: str, limit: int = 10) -> list[dict]:
    """Get team's match history."""
    history = []
    query = (
        db.collection("teams")
        .document(team_id)
        .collection("history")
        .order_by("played_at", direction="DESCENDING")
    )

    for doc in query.stream():
        history.append(doc.to_dict())

    return history[:limit]


def get_team_stats(db: Client, team_id: str) -> dict:
    """Get team statistics."""
    team_doc = teams_collection(db).document(team_id).get()
    if not team_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    team_data = team_doc.to_dict()
    return team_data.get("stats", {
        "total_matches": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "win_rate": 0.0,
        "rating": 1200.0,
        "last_match_at": None,
    })
