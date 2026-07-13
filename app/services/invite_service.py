"""Smart match invitations — tiered candidate ranking + LLM-personalized invite messages.

Tiering (per product decision): default the invite pool to people the captain has already
played with ("playmates"); only fall back to strangers — players currently queued for this
same court/slot, then nearby players who have explicitly opted in — if the playmate pool is
thin.
"""

import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import (
    Booking,
    BookingParticipant,
    MatchInvite,
    MatchRequest,
    PlayerInvitePreference,
    Tenant,
    User,
)
from app.services import notification_service, realtime_service, team_service


def _display_name(db: Session, uid: str) -> str:
    user = db.query(User).filter(User.uid == uid).first()
    return user.display_name if user and user.display_name else uid


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _current_participant_uids(db: Session, booking: Booking) -> set[str]:
    participants = db.query(BookingParticipant).filter(BookingParticipant.booking_id == booking.booking_id).all()
    return {booking.created_by} | {p.uid for p in participants}


def _existing_invite_uids(db: Session, booking_id: str) -> set[str]:
    invites = (
        db.query(MatchInvite)
        .filter(MatchInvite.booking_id == booking_id, MatchInvite.status.in_(["pending", "accepted"]))
        .all()
    )
    return {i.to_uid for i in invites}


def get_invite_candidates(
    db: Session, tenant_id: str, booking_id: str, requester_uid: str, limit: int = 12
) -> list[dict]:
    booking = db.query(Booking).filter(Booking.booking_id == booking_id, Booking.tenant_id == tenant_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    exclude = _current_participant_uids(db, booking) | _existing_invite_uids(db, booking_id) | {requester_uid}
    seen: set[str] = set()
    candidates: list[dict] = []

    # Tier 1: playmates — people who share a past booking (as creator or participant) with the requester.
    my_booking_ids = {b.booking_id for b in db.query(Booking).filter(Booking.created_by == requester_uid).all()}
    my_booking_ids |= {
        p.booking_id for p in db.query(BookingParticipant).filter(BookingParticipant.uid == requester_uid).all()
    }
    if my_booking_ids:
        counts: dict[str, int] = {}
        for b in db.query(Booking).filter(Booking.booking_id.in_(my_booking_ids)).all():
            if b.created_by not in exclude:
                counts[b.created_by] = counts.get(b.created_by, 0) + 1
        for p in db.query(BookingParticipant).filter(BookingParticipant.booking_id.in_(my_booking_ids)).all():
            if p.uid not in exclude:
                counts[p.uid] = counts.get(p.uid, 0) + 1
        for uid, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            if uid in seen or len(candidates) >= limit:
                break
            seen.add(uid)
            candidates.append({
                "uid": uid,
                "display_name": _display_name(db, uid),
                "tier": "playmate",
                "reason": f"Played with you {count}x",
            })

    # Tier 2: queue — players currently waiting for this same court + date.
    if len(candidates) < limit:
        waiting = (
            db.query(MatchRequest)
            .filter(
                MatchRequest.tenant_id == tenant_id,
                MatchRequest.court_id == booking.court_id,
                MatchRequest.date == booking.date,
                MatchRequest.status == "waiting",
            )
            .all()
        )
        for mr in waiting:
            if mr.uid in exclude or mr.uid in seen or len(candidates) >= limit:
                continue
            seen.add(mr.uid)
            candidates.append({
                "uid": mr.uid,
                "display_name": _display_name(db, mr.uid),
                "tier": "queue",
                "reason": "Waiting for a game right now",
            })

    # Tier 3: nearby opted-in players.
    if len(candidates) < limit:
        venue = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        opted_in = db.query(PlayerInvitePreference).filter(PlayerInvitePreference.open_to_invites == True).all()  # noqa: E712
        for pref in opted_in:
            if pref.uid in exclude or pref.uid in seen or len(candidates) >= limit:
                continue
            if pref.preferred_court_ids and booking.court_id not in pref.preferred_court_ids:
                continue
            if not venue:
                continue
            their_venues = {
                b.tenant_id for b in db.query(Booking).filter(Booking.created_by == pref.uid).all()
            }
            in_range = False
            for their_tenant_id in their_venues:
                their_venue = db.query(Tenant).filter(Tenant.tenant_id == their_tenant_id).first()
                if their_venue and _haversine_km(venue.geo_lat, venue.geo_lng, their_venue.geo_lat, their_venue.geo_lng) <= pref.radius_km:
                    in_range = True
                    break
            if not in_range:
                continue
            seen.add(pref.uid)
            candidates.append({
                "uid": pref.uid,
                "display_name": _display_name(db, pref.uid),
                "tier": "nearby",
                "reason": "Open to invites nearby",
            })

    return candidates


def send_invites(db: Session, tenant_id: str, booking_id: str, from_uid: str, invites: list[dict]) -> list[MatchInvite]:
    """invites: list of {"to_uid": str, "tier": str}."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id, Booking.tenant_id == tenant_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.created_by != from_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the booking owner can send invites")

    inviter_name = _display_name(db, from_uid)
    created: list[MatchInvite] = []

    for item in invites:
        to_uid = item["to_uid"]
        tier = item.get("tier", "nearby")
        if to_uid == from_uid:
            continue
        existing = (
            db.query(MatchInvite)
            .filter(MatchInvite.booking_id == booking_id, MatchInvite.to_uid == to_uid)
            .first()
        )
        if existing:
            continue

        title = f"{inviter_name} invited you to play {booking.sport}!"
        body = f"{booking.date} at {booking.start_time}–{booking.end_time}"
        try:
            from app.services.llm_service import generate_notification_message
            message = generate_notification_message("team_invitation", {
                "team_name": booking.team_name or booking.sport.title(),
                "inviter": inviter_name,
                "sport": booking.sport,
            })
            # generate_notification_message swallows its own LLM failures and returns a
            # generic placeholder rather than raising/returning None — detect that case
            # so we fall back to the friendlier template above instead of "SportsOS Update".
            if message and message.get("title") not in (None, "SportsOS Update") and message.get("body"):
                title, body = message["title"], message["body"]
        except Exception:
            pass

        invite = MatchInvite(
            tenant_id=tenant_id,
            booking_id=booking_id,
            from_uid=from_uid,
            to_uid=to_uid,
            tier=tier,
            status="pending",
            title=title,
            body=body,
        )
        db.add(invite)
        db.flush()
        notification_service.record_notification(
            db, to_uid, "match_invite", title, body,
            data={"invite_id": invite.invite_id, "booking_id": booking_id},
        )
        created.append(invite)

    db.commit()
    for invite in created:
        db.refresh(invite)
        realtime_service.mirror_invite_status(invite)
    return created


def respond_to_invite(db: Session, invite_id: str, to_uid: str, accept: bool) -> dict:
    invite = db.query(MatchInvite).filter(MatchInvite.invite_id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.to_uid != to_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your invite")
    if invite.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invite already {invite.status}")

    invite.responded_at = datetime.now(timezone.utc)

    if not accept:
        invite.status = "declined"
        db.commit()
        realtime_service.mirror_invite_status(invite)
        return {"success": True, "status": "declined"}

    booking = db.query(Booking).filter(Booking.booking_id == invite.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    existing_participant = (
        db.query(BookingParticipant)
        .filter(BookingParticipant.booking_id == booking.booking_id, BookingParticipant.uid == to_uid)
        .first()
    )
    if not existing_participant:
        db.add(BookingParticipant(booking_id=booking.booking_id, uid=to_uid, joined_at=datetime.now(timezone.utc)))

    if booking.team_id:
        try:
            team_service.add_team_member(db, booking.team_id, to_uid)
        except HTTPException:
            pass  # already a member

    invite.status = "accepted"
    db.commit()
    realtime_service.mirror_invite_status(invite)
    realtime_service.mirror_match_state(db, booking.tenant_id, booking.booking_id)
    return {"success": True, "status": "accepted", "booking_id": booking.booking_id}


def get_my_pending_invites(db: Session, uid: str) -> list[MatchInvite]:
    return (
        db.query(MatchInvite)
        .filter(MatchInvite.to_uid == uid, MatchInvite.status == "pending")
        .order_by(MatchInvite.created_at.desc())
        .all()
    )


def get_invite_preferences(db: Session, uid: str) -> PlayerInvitePreference:
    pref = db.query(PlayerInvitePreference).filter(PlayerInvitePreference.uid == uid).first()
    if not pref:
        pref = PlayerInvitePreference(uid=uid)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def update_invite_preferences(
    db: Session,
    uid: str,
    open_to_invites: bool | None = None,
    radius_km: float | None = None,
    preferred_court_ids: list[str] | None = None,
) -> PlayerInvitePreference:
    pref = get_invite_preferences(db, uid)
    if open_to_invites is not None:
        pref.open_to_invites = open_to_invites
    if radius_km is not None:
        pref.radius_km = radius_km
    if preferred_court_ids is not None:
        pref.preferred_court_ids = preferred_court_ids
    pref.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pref)
    return pref
