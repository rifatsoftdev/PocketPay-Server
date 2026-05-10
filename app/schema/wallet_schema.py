from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime



# Request and Response Schemas
class SendMoneyRequest(BaseModel):
    access_token: str
    user_id: str
    device_id: str
    device_uuid: str
    user_password: str

    recipient_phone: str
    amount: Decimal
    reference: Optional[str] = None


# Response Schemas
class BalanceResponse(BaseModel):
    balance: float
    currency: str
    last_updated: datetime


# Response Schemas
class TransactionResponse(BaseModel):
    transaction_id: str
    sender: str
    receiver: str
    method: str
    amount: float
    status: str
    created_at: datetime


# Response Schemas
# class TransactionHistoryResponse(BaseModel):
#     transactions: List[TransactionResponse]
#     pagination: dict


# Response Schemas
# class AddMoneyResponse(BaseModel):
#     transaction_id: str
#     amount: float
#     payment_method: str
#     status: str
#     created_at: datetime


# Response Schemas
# class CashOutResponse(BaseModel):
#     transaction_id: str
#     amount: float
#     bank_account: str
#     bank_name: str
#     status: str
#     estimated_completion: datetime 
