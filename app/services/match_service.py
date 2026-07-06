from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.db import Client, FieldFilter, transactional
from app.models.booking import BookingResponse
from app.models.match import MatchResponse, OpenToCommunityRequest, ParticipantResponse
from app.models.venue import GeoPoint
from app.services.booking_service import booking_to_response, bookings_ref
from app.services.venue_service import get_venue
from app.services.wallet_service import wallet_doc_ref, wallet_tx_collection


def open_to_community(
    db: Client, tenant_id: str, booking_id: str, uid: str, req: OpenToCommunityRequest
) -> BookingResponse:
    booking_ref = bookings_ref(db, tenant_id).document(booking_id)
    doc = booking_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    data = doc.to_dict()
    if data["created_by"] != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the captain who booked this slot can open it"
        )
    if data["status"] != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only confirmed bookings can be opened to the community"
        )
    if req.slots_open < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="slots_open must be at least 1")

    venue = get_venue(db, tenant_id)
    updates = {
        "is_joinable": True,
        "slots_total": req.slots_open,
        "slots_open": req.slots_open,
        "tenant_name": venue.name,
        "geo": venue.geo.model_dump(),
    }
    booking_ref.update(updates)
    data.update(updates)
    return booking_to_response(tenant_id, booking_id, data)


def discover_matches(db: Client, sport: str | None = None, date: str | None = None) -> list[MatchResponse]:
    query = (
        db.collection_group("bookings")
        .where(filter=FieldFilter("is_joinable", "==", True))
        .where(filter=FieldFilter("status", "==", "confirmed"))
        .where(filter=FieldFilter("slots_open", ">", 0))
    )
    if sport:
        query = query.where(filter=FieldFilter("sport", "==", sport))
    if date:
        query = query.where(filter=FieldFilter("date", "==", date))

    results = []
    for doc in query.stream():
        tenant_id = doc.reference.parent.parent.id
        data = doc.to_dict()
        base = booking_to_response(tenant_id, doc.id, data)
        results.append(
            MatchResponse(**base.model_dump(), tenant_name=data["tenant_name"], geo=GeoPoint(**data["geo"]))
        )
    return results


@transactional
def _join_match_txn(
    transaction,
    booking_ref,
    participant_ref,
    joiner_wallet_ref,
    joiner_tx_ref,
    captain_wallet_ref,
    captain_tx_ref,
    price_per_slot: float,
) -> dict:
    booking_snapshot = booking_ref.get(transaction=transaction)
    if not booking_snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    data = booking_snapshot.to_dict()
    if not data.get("is_joinable") or data["status"] != "confirmed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This match is not open to join")
    if data.get("slots_open", 0) <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No open slots left")
    if participant_ref.get(transaction=transaction).exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already joined this match")

    joiner_wallet_snap = joiner_wallet_ref.get(transaction=transaction)
    captain_wallet_snap = captain_wallet_ref.get(transaction=transaction)
    if not joiner_wallet_snap.exists or not captain_wallet_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Both players must have a wallet (register as a player) to join or host a match",
        )
    joiner_balance = joiner_wallet_snap.to_dict()["balance"]
    if joiner_balance < price_per_slot:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance to join this match")
    captain_balance = captain_wallet_snap.to_dict()["balance"]

    new_slots_open = data["slots_open"] - 1
    new_joiner_balance = joiner_balance - price_per_slot
    new_captain_balance = captain_balance + price_per_slot
    now = datetime.now(UTC).isoformat()

    transaction.update(booking_ref, {"slots_open": new_slots_open})
    transaction.set(participant_ref, {"joined_at": now})
    transaction.update(joiner_wallet_ref, {"balance": new_joiner_balance})
    transaction.set(
        joiner_tx_ref,
        {
            "type": "debit",
            "amount": price_per_slot,
            "reason": "Joined a community match",
            "related_booking_id": booking_ref.id,
            "balance_after": new_joiner_balance,
            "created_at": now,
        },
    )
    transaction.update(captain_wallet_ref, {"balance": new_captain_balance})
    transaction.set(
        captain_tx_ref,
        {
            "type": "credit",
            "amount": price_per_slot,
            "reason": "Player joined your open match",
            "related_booking_id": booking_ref.id,
            "balance_after": new_captain_balance,
            "created_at": now,
        },
    )

    data["slots_open"] = new_slots_open
    return data


def join_match(db: Client, tenant_id: str, booking_id: str, uid: str) -> BookingResponse:
    booking_ref = bookings_ref(db, tenant_id).document(booking_id)
    doc = booking_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    data = doc.to_dict()
    captain_uid = data["created_by"]
    if captain_uid == uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already own this booking")

    slots_total = data.get("slots_total") or 1
    price_per_slot = round(data["price"] / slots_total, 2)

    participant_ref = booking_ref.collection("participants").document(uid)
    result = _join_match_txn(
        db.transaction(),
        booking_ref,
        participant_ref,
        wallet_doc_ref(db, uid),
        wallet_tx_collection(db, uid).document(),
        wallet_doc_ref(db, captain_uid),
        wallet_tx_collection(db, captain_uid).document(),
        price_per_slot,
    )
    return booking_to_response(tenant_id, booking_id, result)


def list_participants(db: Client, tenant_id: str, booking_id: str) -> list[ParticipantResponse]:
    docs = bookings_ref(db, tenant_id).document(booking_id).collection("participants").stream()
    return [ParticipantResponse(uid=doc.id, joined_at=doc.to_dict()["joined_at"]) for doc in docs]
