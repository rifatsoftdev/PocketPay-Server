
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal





class BankListOut(BaseModel):
    # id: int
    bank_id: str
    bank_logo: Optional[str] = None
    bank_name: str
    description: str

    model_config = {
        "from_attributes": True
    }


class PocketToBankRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str = Field(alias="uuid")
    password: str

    bank_id: str
    bank_account: str
    bank_account_name: Optional[str] = None
    amount: Decimal
    reference: Optional[str] = None

    model_config = {
        "populate_by_name": True
    }


class BankToPocketRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str = Field(alias="uuid")
    password: Optional[str] = None

    bank_id: str
    bank_account: str
    bank_account_name: Optional[str] = None
    amount: Decimal
    reference: Optional[str] = None

    model_config = {
        "populate_by_name": True
    }
