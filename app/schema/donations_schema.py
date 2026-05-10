from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional





class DonationsRequest(BaseModel):
    user_id: str
    access_token: str
    device_id: str
    device_uuid: str
    user_password: str
    
    organization_id: int
    amount: Decimal
    refarence: Optional[str] = None


class DonationOrgRequest(BaseModel):
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    android_id: Optional[str] = None
    android_uuid: Optional[str] = None

    organization_name: str
    description: str
    organization_logo: Optional[str] = None
    organization_api: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    meta_data: Optional[dict] = None


class DonationOrgRemoveRequest(BaseModel):
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    android_id: Optional[str] = None
    android_uuid: Optional[str] = None

    organization_id: int
    


class DonationOut(BaseModel):
    organization_id: int
    organization_name: str
    organization_logo: str
    description: str

    min_amount: Decimal
    max_amount: Decimal

    model_config = ConfigDict(from_attributes=True)
