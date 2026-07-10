from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.db import Client, transactional
from app.models.wallet import WalletResponse, WalletTransactionResponse


def wallet_doc_ref(db: Client, uid: str):
    return db.collection("players").document(uid).collection("wallet").document("wallet")


def wallet_tx_collection(db: Client, uid: str):
    return db.collection("players").document(uid).collection("wallet_transactions")


def get_wallet(db: Client, uid: str) -> WalletResponse:
    doc = wallet_doc_ref(db, uid).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    data = doc.to_dict()
    return WalletResponse(
        uid=uid,
        balance=data["balance"],
        currency=data.get("currency", "INR")
    )


def list_transactions(db: Client, uid: str) -> list[WalletTransactionResponse]:
    docs = wallet_tx_collection(db, uid).order_by("created_at", direction="DESCENDING").stream()
    return [WalletTransactionResponse(tx_id=doc.id, **doc.to_dict()) for doc in docs]


@transactional
def _apply_ledger_entry(transaction, wallet_ref, tx_ref, amount: float, tx_type: str, reason: str, related_booking_id: str | None) -> float:
    snapshot = wallet_ref.get(transaction=transaction)
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    data = snapshot.to_dict()
    balance = data["balance"]
    currency = data.get("currency", "INR")
    if tx_type == "debit" and balance < amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance")
    new_balance = balance - amount if tx_type == "debit" else balance + amount
    transaction.update(wallet_ref, {"balance": new_balance})
    transaction.set(
        tx_ref,
        {
            "type": tx_type,
            "amount": amount,
            "currency": currency,
            "reason": reason,
            "related_booking_id": related_booking_id,
            "balance_after": new_balance,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return new_balance


def credit_wallet(db: Client, uid: str, amount: float, reason: str, related_booking_id: str | None = None) -> float:
    wallet_ref = wallet_doc_ref(db, uid)
    tx_ref = wallet_tx_collection(db, uid).document()
    return _apply_ledger_entry(db.transaction(), wallet_ref, tx_ref, amount, "credit", reason, related_booking_id)


def debit_wallet(db: Client, uid: str, amount: float, reason: str, related_booking_id: str | None = None) -> float:
    wallet_ref = wallet_doc_ref(db, uid)
    tx_ref = wallet_tx_collection(db, uid).document()
    return _apply_ledger_entry(db.transaction(), wallet_ref, tx_ref, amount, "debit", reason, related_booking_id)
