import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.orm import Wallet, WalletTransaction
from app.models.wallet import WalletResponse, WalletTransactionResponse


def get_wallet(db: Session, uid: str) -> WalletResponse:
    wallet = db.query(Wallet).filter(Wallet.uid == uid).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return WalletResponse(uid=uid, balance=wallet.balance, currency=wallet.currency)


def list_transactions(db: Session, uid: str) -> list[WalletTransactionResponse]:
    txs = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.uid == uid)
        .order_by(WalletTransaction.created_at.desc())
        .all()
    )
    return [
        WalletTransactionResponse(
            tx_id=tx.tx_id,
            type=tx.type,
            amount=tx.amount,
            currency=tx.currency,
            reason=tx.reason,
            related_booking_id=tx.related_booking_id,
            balance_after=tx.balance_after,
            created_at=tx.created_at.isoformat(),
        )
        for tx in txs
    ]


def credit_wallet(
    db: Session, uid: str, amount: float, reason: str, related_booking_id: str | None = None
) -> float:
    return _apply_ledger_entry(db, uid, amount, "credit", reason, related_booking_id)


def debit_wallet(
    db: Session, uid: str, amount: float, reason: str, related_booking_id: str | None = None
) -> float:
    return _apply_ledger_entry(db, uid, amount, "debit", reason, related_booking_id)


def _apply_ledger_entry(
    db: Session,
    uid: str,
    amount: float,
    tx_type: str,
    reason: str,
    related_booking_id: str | None,
) -> float:
    wallet = db.query(Wallet).filter(Wallet.uid == uid).with_for_update().first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    if tx_type == "debit" and wallet.balance < amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance")
    new_balance = wallet.balance - amount if tx_type == "debit" else wallet.balance + amount
    wallet.balance = new_balance
    tx = WalletTransaction(
        tx_id=uuid.uuid4().hex,
        uid=uid,
        type=tx_type,
        amount=amount,
        currency=wallet.currency,
        reason=reason,
        related_booking_id=related_booking_id,
        balance_after=new_balance,
        created_at=datetime.now(timezone.utc),
    )
    db.add(tx)
    # Caller is responsible for db.commit()
    return new_balance
