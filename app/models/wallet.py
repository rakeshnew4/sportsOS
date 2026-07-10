from typing import Literal

from pydantic import BaseModel

TransactionType = Literal["credit", "debit"]
Currency = Literal["INR", "USD", "EUR"]


class WalletResponse(BaseModel):
    uid: str
    balance: float
    currency: str = "INR"  # Default to INR (1 credit = 1 rupee)


class WalletTransactionResponse(BaseModel):
    tx_id: str
    type: TransactionType
    amount: float
    currency: str = "INR"
    reason: str
    related_booking_id: str | None = None
    balance_after: float
    created_at: str
