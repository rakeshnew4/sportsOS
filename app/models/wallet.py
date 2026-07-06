from typing import Literal

from pydantic import BaseModel

TransactionType = Literal["credit", "debit"]


class WalletResponse(BaseModel):
    uid: str
    balance: float


class WalletTransactionResponse(BaseModel):
    tx_id: str
    type: TransactionType
    amount: float
    reason: str
    related_booking_id: str | None = None
    balance_after: float
    created_at: str
