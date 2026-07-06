"""True "Join Match" — PUBG-style matchmaking, distinct from Hybrid Booking
(match_service.py). No captain, no pre-existing booking: players individually
queue for a specific open court slot, and once enough of them (per-sport
MIN_PLAYERS) are queued for the exact same slot, the system itself forms a
real booking, splits the cost, and debits each matched player's wallet.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.db import Client, FieldFilter, transactional
from app.models.matchmaking import MatchRequestCreate, MatchRequestResponse
from app.services.booking_service import bookings_ref, slot_overlaps_existing, to_minutes
from app.services.court_service import get_court
from app.services.wallet_service import wallet_doc_ref, wallet_tx_collection

MIN_PLAYERS = {
    "badminton": 4,
    "tennis": 2,
    "table_tennis": 2,
    "cricket": 10,
    "football": 10,
    "volleyball": 6,
    "basketball": 6,
}
DEFAULT_MIN_PLAYERS = 4


def _min_players_for(sport: str) -> int:
    return MIN_PLAYERS.get(sport, DEFAULT_MIN_PLAYERS)


def match_requests_ref(db: Client, tenant_id: str):
    return db.collection("tenants").document(tenant_id).collection("match_requests")


def _to_response(tenant_id: str, request_id: str, data: dict, current_count: int) -> MatchRequestResponse:
    return MatchRequestResponse(
        request_id=request_id,
        tenant_id=tenant_id,
        court_id=data["court_id"],
        sport=data["sport"],
        date=data["date"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        uid=data["uid"],
        status=data["status"],
        min_players=data["min_players"],
        current_count=current_count,
        matched_booking_id=data.get("matched_booking_id"),
    )


def _waiting_requests_for_slot(db: Client, tenant_id: str, court_id: str, date: str, start_time: str, end_time: str):
    docs = (
        match_requests_ref(db, tenant_id)
        .where(filter=FieldFilter("court_id", "==", court_id))
        .where(filter=FieldFilter("date", "==", date))
        .where(filter=FieldFilter("start_time", "==", start_time))
        .where(filter=FieldFilter("end_time", "==", end_time))
        .where(filter=FieldFilter("status", "==", "waiting"))
        .stream()
    )
    return sorted(docs, key=lambda d: d.to_dict()["created_at"])


@transactional
def _form_match_txn(transaction, request_refs, booking_ref, wallet_refs, tx_refs, court_id, sport, date, start_time, end_time, price) -> str | None:
    request_snaps = [ref.get(transaction=transaction) for ref in request_refs]
    if not all(s.exists and s.to_dict()["status"] == "waiting" for s in request_snaps):
        return None  # a concurrent call already matched or cancelled one of these

    wallet_snaps = [ref.get(transaction=transaction) for ref in wallet_refs]
    if not all(s.exists for s in wallet_snaps):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="All matched players must have a wallet (register as a player) to be matched",
        )

    count = len(request_refs)
    share = round(price / count, 2)
    if any(snap.to_dict()["balance"] < share for snap in wallet_snaps):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One of the matched players doesn't have enough wallet balance for their share",
        )

    now = datetime.now(UTC).isoformat()
    first_uid = request_snaps[0].to_dict()["uid"]

    booking_data = {
        "court_id": court_id,
        "sport": sport,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "price": price,
        "status": "confirmed",
        "created_by": first_uid,
        "is_joinable": False,
        "slots_total": count,
        "slots_open": 0,
        "tenant_name": None,
        "geo": None,
        "created_at": now,
    }
    transaction.set(booking_ref, booking_data)

    for req_ref, req_snap, wallet_ref, wallet_snap, tx_ref in zip(request_refs, request_snaps, wallet_refs, wallet_snaps, tx_refs):
        uid = req_snap.to_dict()["uid"]
        new_balance = wallet_snap.to_dict()["balance"] - share
        transaction.update(wallet_ref, {"balance": new_balance})
        transaction.set(
            tx_ref,
            {
                "type": "debit",
                "amount": share,
                "reason": "Matched into a Join Match game",
                "related_booking_id": booking_ref.id,
                "balance_after": new_balance,
                "created_at": now,
            },
        )
        transaction.set(booking_ref.collection("participants").document(uid), {"joined_at": now})
        transaction.update(req_ref, {"status": "matched", "matched_booking_id": booking_ref.id})

    return booking_ref.id


def create_match_request(db: Client, tenant_id: str, uid: str, req: MatchRequestCreate) -> MatchRequestResponse:
    court = get_court(db, tenant_id, req.court_id)
    if not court.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Court is not active")

    start_min, end_min = to_minutes(req.start_time), to_minutes(req.end_time)
    if end_min <= start_min:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")
    if start_min < to_minutes(court.open_time) or end_min > to_minutes(court.close_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Requested time is outside court operating hours"
        )

    if slot_overlaps_existing(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This slot is already booked")

    already_waiting = _waiting_requests_for_slot(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time)
    if any(d.to_dict()["uid"] == uid for d in already_waiting):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You're already queued for this slot")

    min_players = _min_players_for(court.sport)
    request_ref = match_requests_ref(db, tenant_id).document()
    data = {
        "court_id": req.court_id,
        "sport": court.sport,
        "date": req.date,
        "start_time": req.start_time,
        "end_time": req.end_time,
        "uid": uid,
        "status": "waiting",
        "min_players": min_players,
        "matched_booking_id": None,
        "created_at": datetime.now(UTC).isoformat(),
    }
    request_ref.set(data)

    waiting = _waiting_requests_for_slot(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time)
    count_for_response = len(waiting)

    if len(waiting) >= min_players:
        duration_hours = (end_min - start_min) / 60
        price = round(court.hourly_price * duration_hours, 2)
        request_refs = [d.reference for d in waiting]
        wallet_refs = [wallet_doc_ref(db, d.to_dict()["uid"]) for d in waiting]
        tx_refs = [wallet_tx_collection(db, d.to_dict()["uid"]).document() for d in waiting]
        booking_ref = bookings_ref(db, tenant_id).document()

        formed_booking_id = _form_match_txn(
            db.transaction(),
            request_refs,
            booking_ref,
            wallet_refs,
            tx_refs,
            req.court_id,
            court.sport,
            req.date,
            req.start_time,
            req.end_time,
            price,
        )
        if formed_booking_id is None:
            count_for_response = len(
                _waiting_requests_for_slot(db, tenant_id, req.court_id, req.date, req.start_time, req.end_time)
            )

    final_doc = request_ref.get().to_dict()
    return _to_response(tenant_id, request_ref.id, final_doc, count_for_response)


def list_match_requests(db: Client, tenant_id: str, court_id: str, date: str) -> list[MatchRequestResponse]:
    docs = list(
        match_requests_ref(db, tenant_id)
        .where(filter=FieldFilter("court_id", "==", court_id))
        .where(filter=FieldFilter("date", "==", date))
        .stream()
    )
    waiting_counts: dict[tuple[str, str], int] = {}
    for doc in docs:
        data = doc.to_dict()
        if data["status"] == "waiting":
            key = (data["start_time"], data["end_time"])
            waiting_counts[key] = waiting_counts.get(key, 0) + 1

    results = []
    for doc in docs:
        data = doc.to_dict()
        key = (data["start_time"], data["end_time"])
        current = waiting_counts.get(key, 0) if data["status"] == "waiting" else data["min_players"]
        results.append(_to_response(tenant_id, doc.id, data, current))
    return results


def cancel_match_request(db: Client, tenant_id: str, request_id: str, uid: str) -> MatchRequestResponse:
    ref = match_requests_ref(db, tenant_id).document(request_id)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match request not found")
    data = doc.to_dict()
    if data["uid"] != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your match request")
    if data["status"] != "waiting":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request already {data['status']}")
    ref.update({"status": "cancelled"})
    data["status"] = "cancelled"
    return _to_response(tenant_id, request_id, data, 0)
