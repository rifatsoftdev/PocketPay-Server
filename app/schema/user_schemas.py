from pydantic import BaseModel

# 
class KYCRequest(BaseModel):
    user_id: str
    access_token: str
    device_id: str
    device_uuid: str

    document_type: str