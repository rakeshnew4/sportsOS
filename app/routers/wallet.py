from fastapi import APIRouter, Depends

from app.core.db import Client, get_db
from app.core.security import CurrentUser, get_current_user
from app.models.wallet import WalletResponse, WalletTransactionResponse
from app.services import wallet_service

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/me")
def get_my_wallet(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> WalletResponse:
    return wallet_service.get_wallet(db, user.uid)


@router.get("/me/transactions")
def list_my_transactions(
    user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> list[WalletTransactionResponse]:
    return wallet_service.list_transactions(db, user.uid)
