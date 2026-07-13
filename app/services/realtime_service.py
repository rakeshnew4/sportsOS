"""Firestore real-time mirroring + FCM push notifications.

Postgres remains the source of truth for everything. This module writes
best-effort, non-blocking mirror documents to Firestore so clients can
subscribe to live updates instead of polling, and sends push notifications
via FCM. Every function here swallows its own errors — a Firestore/FCM
outage (or Firebase simply not being configured on this deployment) must
never fail the booking/join/invite/notification request that triggered it.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.firebase import get_auth, get_firestore_client, get_messaging
from app.db.orm import Booking, BookingParticipant, DeviceToken, MatchInvite

logger = logging.getLogger(__name__)


def mint_custom_token(uid: str) -> str | None:
    auth_mod = get_auth()
    if auth_mod is None:
        return None
    try:
        return auth_mod.create_custom_token(uid).decode("utf-8")
    except Exception:
        logger.exception("Failed to mint Firebase custom token for uid=%s", uid)
        return None


def mirror_match_state(db: Session, tenant_id: str, booking_id: str) -> None:
    client = get_firestore_client()
    if client is None:
        return
    try:
        booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            return
        participants = (
            db.query(BookingParticipant)
            .filter(BookingParticipant.booking_id == booking_id)
            .all()
        )
        client.collection("matches").document(booking_id).set({
            "tenant_id": tenant_id,
            "court_id": booking.court_id,
            "date": booking.date,
            "status": booking.status,
            "is_joinable": booking.is_joinable,
            "slots_total": booking.slots_total,
            "slots_open": booking.slots_open,
            "participants": [
                {"uid": p.uid, "display_name": p.display_name} for p in participants
            ],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("Failed to mirror match state for booking_id=%s", booking_id)


def mirror_invite_status(invite: MatchInvite) -> None:
    client = get_firestore_client()
    if client is None:
        return
    try:
        (
            client.collection("matches")
            .document(invite.booking_id)
            .collection("invites")
            .document(invite.invite_id)
            .set({
                "to_uid": invite.to_uid,
                "from_uid": invite.from_uid,
                "status": invite.status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        )
    except Exception:
        logger.exception("Failed to mirror invite status for invite_id=%s", invite.invite_id)


def mirror_slot_availability(db: Session, tenant_id: str, court_id: str, date: str) -> None:
    client = get_firestore_client()
    if client is None:
        return
    try:
        from app.services.booking_service import ACTIVE_STATUSES

        existing = (
            db.query(Booking)
            .filter(
                Booking.tenant_id == tenant_id,
                Booking.court_id == court_id,
                Booking.date == date,
                Booking.status.in_(list(ACTIVE_STATUSES)),
            )
            .all()
        )
        booked_ranges = [{"start_time": b.start_time, "end_time": b.end_time} for b in existing]
        doc_id = f"{tenant_id}_{court_id}_{date}"
        client.collection("slots").document(doc_id).set({
            "tenant_id": tenant_id,
            "court_id": court_id,
            "date": date,
            "booked_ranges": booked_ranges,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("Failed to mirror slot availability for %s/%s/%s", tenant_id, court_id, date)


def send_push(db: Session, uid: str, title: str, body: str, data: dict | None = None) -> None:
    messaging_mod = get_messaging()
    if messaging_mod is None:
        return
    try:
        tokens = db.query(DeviceToken).filter(DeviceToken.uid == uid).all()
        if not tokens:
            return
        str_data = {k: str(v) for k, v in (data or {}).items()}
        message = messaging_mod.MulticastMessage(
            notification=messaging_mod.Notification(title=title, body=body),
            data=str_data,
            tokens=[t.token for t in tokens],
        )
        response = messaging_mod.send_each_for_multicast(message)
        stale_token_ids = [
            token_row.id
            for token_row, result in zip(tokens, response.responses)
            if not result.success
            and isinstance(result.exception, (messaging_mod.UnregisteredError, messaging_mod.SenderIdMismatchError))
        ]
        if stale_token_ids:
            db.query(DeviceToken).filter(DeviceToken.id.in_(stale_token_ids)).delete(synchronize_session=False)
            db.commit()
    except Exception:
        logger.exception("Failed to send push notification to uid=%s", uid)


def register_device_token(db: Session, uid: str, platform: str, token: str) -> None:
    existing = db.query(DeviceToken).filter(DeviceToken.uid == uid, DeviceToken.token == token).first()
    now = datetime.now(timezone.utc)
    if existing:
        existing.last_seen_at = now
        existing.platform = platform
    else:
        db.add(DeviceToken(uid=uid, platform=platform, token=token, created_at=now, last_seen_at=now))
    db.commit()


def unregister_device_token(db: Session, uid: str, token: str) -> None:
    db.query(DeviceToken).filter(DeviceToken.uid == uid, DeviceToken.token == token).delete()
    db.commit()
