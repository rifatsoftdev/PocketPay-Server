from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


# # Profile Update Request
# class ProfileUpdateRequest(BaseModel):
#     user_id: str
#     access_token: str
#     android_id: str
#     android_uuid: str

#     full_name: Optional[str] = None
#     gender: Optional[str] = None
#     date_of_birth: Optional[datetime] = None
#     avatar_url: Optional[str] = None


# TOTP activation
class TOTPVerifyRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str
    totp_code: str
    secret: str


# TOTP disable request
class TOTPDisableRequest(BaseModel):
    user_id: str
    access_token: str
    android_id: str
    android_uuid: str
    user_password: str
