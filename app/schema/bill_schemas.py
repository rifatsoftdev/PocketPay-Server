from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.enums.enums import BillCategory


class BillCategoryResponse(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    status: str


class BillCategoriesResponse(BaseModel):
    categories: List[BillCategoryResponse]


class PayBillRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: Optional[str] = None
    android_uuid: Optional[str] = None
    user_password: str

    category: str
    company_id: str
    bill_account: str
    amount: Decimal
    reference: Optional[str] = None



class BillProviderCreateRequest(BaseModel):
    user_id: str
    access_token: str
    device_id: str
    device_uuid: str
    user_password: str

    category: BillCategory
    company_name: str
    description: str
    company_logo: Optional[str] = None
    company_api: Optional[str] = None
    company_user_id: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None



class BillProviderOut(BaseModel):
    # id: int
    category: BillCategory
    company_id: int
    company_logo: Optional[str] = None
    company_name: str
    description: str
    is_gateway: bool
    min_amount: Optional[float]
    max_amount: Optional[float]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }


class BillHistoryRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str
    status: Optional[str] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    page: int = 1
    limit: int = 20


class BillTransactionDetailsRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str
    transaction_id: str


class BillValidateRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str
    category: str
    company_id: int
    bill_account: str
    amount: Decimal
