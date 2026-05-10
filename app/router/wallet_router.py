from fastapi import APIRouter, Depends, BackgroundTasks, Header, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import HistoryServices
from app.schema import SendMoneyRequest, GlobalResponse
from app.utils import Generators, Helpers

from app.services.wallet.wallet_service import UserVerificationService, WalletService





wallet_router = APIRouter()



# ==============================================================================

@wallet_router.get("/balance")
async def get_balance(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """Get user wallet balance."""
    walletService = WalletService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return walletService.get_balance()




# ==============================================================================

@wallet_router.post("/sent-money")
async def send_money(
    payload: SendMoneyRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """Send money to another user."""
    wallet_service = WalletService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return wallet_service.send_money(payload=payload)




# ==============================================================================

@wallet_router.get("/transaction-details/{transaction_id}")
async def transaction_details(
    transaction_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    historyServices = HistoryServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return historyServices.transaction_details(transaction_id=transaction_id)




# ==============================================================================
# ==============================================================================
