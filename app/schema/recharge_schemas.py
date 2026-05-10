from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class MobileRechargeRequest(BaseModel):
    user_id: str
    access_token: str
    device_id: str
    device_uuid: str
    user_password: str
    
    operator_id: str
    number: str
    amount: Decimal
    refarence: Optional[str] = None



class OperatorOut(BaseModel):
    operator_id: str
    operator_name: str
    country_code: str
    logo_url: str

    model_config = {
        "from_attributes": True
    }



class NewOperatorRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str
    user_password: str

    operator_name: str
    country_code: str
    logo_url: str
    operator_api: str


class OperatorDeactivateRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str
    user_password: str

    operator_id: str
    
    
