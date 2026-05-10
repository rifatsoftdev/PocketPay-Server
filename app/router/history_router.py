from fastapi import APIRouter, Depends, BackgroundTasks, Request, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.constants import AnsiColor, String

from app.services.auth.user_verification import UserVerificationService
from app.services import HistoryServices
from app.utils import Helpers

from app.schema.global_schema import GlobalRequest, GlobalResponse



history_router = APIRouter()



# ==============================================================================
"""
Get All Transactions

request example
post {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid"
}

response example
{
    "success": true,
    "message": "Last 100 transactions fetched successfully",
    "data": {
        "transactions": [
            {
                "transaction_id": "TXN20260131121347UDOZFN",
                "transaction_type": "sendmoney",
                "method": "wallet",
                "sender_user_id": "274051a6-aa9c-4a23-96d5-279797faa282",
                "receiver_user_id": "89eb4658-a1a6-40d2-845a-835f5d8a14e3",
                "sender_account": "8801XXXXXXXXX",
                "receiver_account": "8801YYYYYYYYY",
                "currency": "BDT",
                "amount": 10.0,
                "service_charge": 1.0,
                "reference": "Gifts",
                "direction": "out",
                "status": "success",
                "created_at": "2026-01-31T06:13:47"
            },
            {
                "transaction_id": "TXN20260131115954FBAKFW",
                "transaction_type": "sendmoney",
                "method": "wallet",
                "sender_user_id": "274051a6-aa9c-4a23-96d5-279797faa282",
                "receiver_user_id": "89eb4658-a1a6-40d2-845a-835f5d8a14e3",
                "sender_account": "8801XXXXXXXXX",
                "receiver_account": "8801YYYYYYYYY",
                "currency": "BDT",
                "amount": 10.0,
                "service_charge": 1.0,
                "reference": "Gifts",
                "direction": "out",
                "status": "success",
                "created_at": "2026-01-31T05:59:54"
            }
        ]
    }
}
"""
# ==============================================================================

@history_router.get("/all-transactions")
async def all_transactions(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    access_token = Helpers.authorization(authorization)

    # verify user
    userVerificationService = UserVerificationService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    user_id: str = userVerificationService.verify_access_token(access_token=access_token)   

    historyServices = HistoryServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )
    return historyServices.all_transactions(user_id)





# ==============================================================================
"""
Get All Notifications

request example
post {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid"
}

response example
{
    "success": true,
    "message": "All notifications fetched successfully",
    "data": {
    "notifications": [
        {
            "id": 3,
            "type": "alert",
            "title": "Welcome to PocketPay! 🔐",
            "body": "Your account has been successfully set up. Your security is our priority.",
            "img_url": null,
            "created_at": "2026-01-31T05:25:08",
            "is_read": false
        }
    ]
    }
}
"""
# ==============================================================================

@history_router.post("/all-notifications")
async def all_notifications(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    access_token = Helpers.authorization(authorization)

    # verify user
    userVerificationService = UserVerificationService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    user_id: str = userVerificationService.verify_access_token(access_token=access_token)   

    historyServices = HistoryServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )
    
    return historyServices.all_notifications(user_id)






# ==============================================================================
# ==============================================================================
