from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Header
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.constants.string import String
from app.constants.colors import AnsiColor
from app.constants.env import ENV

from app.core.database import get_db

from app.enums.transactions_enum import TransactionType, TransactionStatus, TransactionDirection
from app.enums.notification_enum import NotificationType

from app.enums import PaymentMethods, ActivityStatus

from app.model.bank_table import BankTable
from app.model.wallet_table import WalletTable
from app.model.transaction_table import TransactionTable

from app.schema.bank_schema import BankListOut, PocketToBankRequest, BankToPocketRequest
from app.schema.global_schema import GlobalResponse

from app.services.auth.user_verification import UserVerificationService
from app.utils.generators import Generators
from app.services.notification.noticication_services import NotificationServices, NotificationData
from app.utils.helpers import utc6dhaka

from app.services import BankServises




bank_router = APIRouter()




# ==============================================================================
"""
Get Banks List

request example
get /banks

response example
{
    "success": true,
    "message": "Bank list fetched successfully",
    "data": {
        "banks": [
            {
                "bank_id": "bank_id",
                "bank_logo": "bank_logo",
                "bank_name": "bank_name",
                "description": "description"
            }
        ]
    }
}
"""
# ==============================================================================

@bank_router.get("/banks")
async def get_banks(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    bankServises = BankServises(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return bankServises.get_banks()



# ==============================================================================
"""
Transfer money from pocket wallet to bank account

request example
post /pocket2bank
{
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "password": "password",

    "bank_id": "bank_id",
    "bank_account": "bank_account",
    "bank_account_name": "bank_account_name",
    "amount": "amount",
    "reference": "reference"
}

response example
{
    "success": true,
    "message": "Pocket to bank transfer successful",
    "data": {
        "transaction_id": "transaction_id",
        "amount": "amount",
        "status": "status"
    }
}

"""
# ==============================================================================

@bank_router.post("/pocket2bank")
async def pocket_to_bank(
    payload: PocketToBankRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Transfer money from pocket wallet to bank account."""
    bankServises = BankServises(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return bankServises.pocket_to_bank(payload=payload)






# ==============================================================================
"""
Bank to pocket transfer

request example
post /bank2pocket
{
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "password": "password",

    "bank_id": "bank_id",
    "bank_account": "bank_account",
    "bank_account_name": "bank_account_name",
    "amount": "amount",
    "reference": "reference"
}

response example
{
    "success": true,
    "message": "Bank to pocket transfer successful",
    "data": {
        "transaction_id": "transaction_id",
        "amount": "amount",
        "status": "status"
    }
}

"""
# ==============================================================================

@bank_router.post("/bank2pocket")
async def bank_to_pocket(
    payload: BankToPocketRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Transfer money from bank account to pocket wallet."""
    bankServises = BankServises(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return bankServises.bank_to_pocket(payload=payload)


