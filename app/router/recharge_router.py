from fastapi import APIRouter, Depends, BackgroundTasks, Request, Header
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.enums.notification_enum import NotificationType

from app.schema.recharge_schemas import OperatorOut, MobileRechargeRequest, NewOperatorRequest, OperatorDeactivateRequest, OperatorActivateRequest
from app.schema.global_schema import GlobalResponse

from app.utils.generators import Generators
from app.services.auth.user_verification import UserVerificationService
from app.utils.notification_manager import NotificationManager
from app.services import RechargeServices
from app.services.wallet.wallet_service import WalletService

from app.enums import ActivityStatus, TransactionType, TransactionStatus, TransactionDirection, PaymentMethods
from app.model import WalletTable, TransactionTable, MobileOperatorTable



recharge_router = APIRouter()




# ==============================================================================

@recharge_router.get("/operators")
async def get_operators(
    request: Request,
    background_tasks: BackgroundTasks,
    country_code: str | None = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get all mobile operators."""
    rechargeServices = RechargeServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return rechargeServices.get_operators(country_code=country_code)




# ==============================================================================

@recharge_router.post("/recharge")
async def mobile_recharge(
    payload: MobileRechargeRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Pay bill endpoint."""
    rechargeServices = RechargeServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return rechargeServices.mobile_recharge(payload=payload)




# ==============================================================================

@recharge_router.post("/new-operator")
async def add_new_operator(
    payload: NewOperatorRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Add new mobile operator."""
    
    rechargeServices = RechargeServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return rechargeServices.add_new_operator(payload=payload)




# ==============================================================================

@recharge_router.post("/deactivate-operator")
async def deactivate_operator(
    payload: OperatorDeactivateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    
    rechargeServices = RechargeServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return rechargeServices.deactivate_operator(payload=payload)




@recharge_router.post("/activate-operator")
async def activate_operator(
    payload: OperatorActivateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    
    rechargeServices = RechargeServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return rechargeServices.activate_operator(payload=payload)



# ==============================================================================
# ==============================================================================
