from fastapi import APIRouter, Depends, BackgroundTasks, Header
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schema import (
    GlobalResponse, FCMTokenRequest, ForgetPasswordRequest, GoogleLoginRequest,
    LoginRequest, RegisterRequest, OTPRequest, VerifyOTPRequest, LogoutAllRequest,
    ChangePasswordRequest, CancelDeleteAccountRequest, LinkGoogleAccountRequest,
    DeleteAccountRequest, ResetPasswordRequest, LogoutRequest, TOTPSetupRequest,
    TOTPConfirmRequest, TOTPAuthDisableRequest, EmailTFASetupRequest,
    EmailTFAConfirmRequest, EmailTFADisableRequest, AccessTokenRequest,
    FinalSetupRequest
)
from app.services import (
    GoogleOauth, TFAServices,
    RegistrationService,
    PasswordService, AccountServices
)




auth_router = APIRouter()




# ==============================================================================

@auth_router.post("/google-login")
async def google_login(
    payload: GoogleLoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    google0auth = GoogleOauth(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return google0auth.google_login(payload=payload)




# ==============================================================================

@auth_router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """User login endpoint."""
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.login(payload=payload)

    


# ==============================================================================

@auth_router.post("/logout")
async def logout(
    payload: LogoutRequest, 
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.logout(payload=payload)




# ==============================================================================
"""
User registration

request example
post {
    "full_name": "David",
    "email_address": "david@gmail.com",
    "phone_number": "01812345677",
    "country_code": "+88",
    "user_password": "1s22s22p6",
    "device_id": "android_id",
    "device_uuid": "android_uuid"
}

{
    "success": true,
    "message": "Registration successful. Please verify with the OTP sent to your phone.",
    "data": {
        "sent_otp": false
    }
}
"""
# ==============================================================================

@auth_router.post("/register", response_model=GlobalResponse)
async def register(
    payload: RegisterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    registrationService = RegistrationService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return registrationService.register(payload=payload)




@auth_router.post("/final-setup", response_model=GlobalResponse)
async def final_setup(
    payload: FinalSetupRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    registrationService = RegistrationService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return registrationService.final_setup(payload=payload)




# ==============================================================================
"""
Send OTP
request example
post {
    "method": "email",
    "delever_to": "david@gmail.com",
    "android_id": "android_id",
    "android_uuid": "android_uuid"
}

response example
{
    "success": true,
    "message": "OTP resent successfully",
    "data": {
        "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZXRob2QiOiJlbWFpbCIsImRlbGV2ZXJfdG8iOiJkYXZpZEBnbWFpbC5jb20iLCJhbmRyb2lkX2lkIjoiYW5kcm9pZF9pZCIsInV1aWQiOiJ1dWlkIiwiZXhwIjoxNzY5ODM3NTIzLCJ0eXBlIjoib3RwIn0.TLvQbcZel74bvBD4YLz3YXVJ-YSQpkqu_953Km6fjxg"
    }
}
"""
# ==============================================================================

@auth_router.post("/send-otp", response_model=GlobalResponse)
async def send_otp(
    payload: OTPRequest, 

    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.send_otp(payload=payload)




# ==============================================================================
"""
Verify OTP

request example
post {
    "method": "email",
    "delever_to": "david@gmail.com",
    "otp": "otp",
    "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZXRob2QiOiJlbWFpbCIsImRlbGV2ZXJfdG8iOiJkYXZpZEBnbWFpbC5jb20iLCJhbmRyb2lkX2lkIjoiYW5kcm9pZF9pZCIsInV1aWQiOiJ1dWlkIiwiZXhwIjoxNzY5ODM3NTIzLCJ0eXBlIjoib3RwIn0.TLvQbcZel74bvBD4YLz3YXVJ-YSQpkqu_953Km6fjxg",
    "android_id": "android_id",
    "android_uuid": "android_uuid"
}

response example
{
    "success": true,
    "message": "OTP verified successfully",
    "data": {
        "user_id": "89eb4658-a1a6-40d2-845a-835f5d8a14e3",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiODllYjQ2NTgtYTFhNi00MGQyLTg0NWEtODM1ZjVkOGExNGUzIiwiZW1haWwiOiJkYXZpZEBnbWFpbC5jb20iLCJhbmRyb2lkX2lkIjoiYW5kcm9pZF9pZCIsInV1aWQiOiJ1dWlkIiwiZXhwIjoxNzcyNDI5MzgwLCJ0eXBlIjoicmVmcmVzaCJ9.ybwh6AYElMWMRWVWS9Q1cwFTUG5hGDSp_tnujowR7RY",
        "email_address": "david@gmail.com",
        "phone_number": "+881812345677"
    }
}
"""
# ==============================================================================

@auth_router.post("/verify-otp", response_model=GlobalResponse)
async def verify_otp(
    payload: VerifyOTPRequest, 
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.verify_otp(payload=payload)




# ==============================================================================
"""
Receive FCM token

request example
post {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "fcm_token": "fcm_token"
}

response example
{
    "success": true,
    "message": "FCM token received successfully",
    "data": {}
}
"""
# ==============================================================================

@auth_router.post("/send-fcm-token")
async def receive_fcm_token(
    payload: FCMTokenRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.receive_fcm_token(payload=payload)



# ==============================================================================
"""
Refresh token

request example
post {
    "refresh_token": "refresh_token"
    "user_id": "user_id",
    "android_id": "android_id",
    "android_uuid": "android_uuid"
}

response example
{
    "success": true,
    "message": "Access token refreshed successfully",
    "data": {
        "access_token": "access_token"
    }
}
"""
# ==============================================================================

@auth_router.post("/new-access-token")
async def access_token(
    payload: AccessTokenRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.get_new_access_token(payload=payload)




# ==============================================================================
"""
Forgetion password

request example
post {
    "email_address": "david@gmail.com",
    "android_id": "android_id",
    "android_uuid": "android_uuid"
}

response example
{
    "success": true,
    "message": "Password reset link sent successfully",
    "data": {}
"""
# ==============================================================================

@auth_router.post("/reset-password")
def reset_password(
    payload: ForgetPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    passwordService = PasswordService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return passwordService.reset_password(payload=payload)




# ==============================================================================
"""
Reset password link

request example
get -/reset-password/{password_token}

response example

"""
# ==============================================================================

@auth_router.get("/reset-password/{password_token}", response_class=HTMLResponse)
def reset_password_page(
    request: Request, 
    password_token: str,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    passwordService = PasswordService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return passwordService.reset_password_page(password_token=password_token)




# ==============================================================================
"""
Set New Password

request example
post {
    "password_token": "password_token",
    "new_password": "new_password",
}

response example
{
    "success": true,
    "message": "Password reset successful",
    "data": {}
}
"""
# ==============================================================================

@auth_router.post("/set-password")
def set_password(
    payload: ResetPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    passwordService = PasswordService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return passwordService.set_password(payload=payload)




# ==============================================================================
"""
Delete Account

request example
post {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "user_password": "user_password",
    "reason": "reason"
}

response example
{
    "success": true,
    "message": "Delete request submitted successfully",
    "data": {
        "scheduled_delete_at": "scheduled_delete_at"
    }
}

"""
# ==============================================================================

@auth_router.post("/delete-account")
def delete_account(
    payload: DeleteAccountRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.delete_account(payload=payload)




# ==============================================================================
"""
Cancel Delete Account

request example
post {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "password": "password"
}

response example
{
    "success": true,
    "message": "Delete request cancelled successfully",
    "data": {}
}
"""
# ==============================================================================

@auth_router.post("/cancel-delete")
def cancel_delete_account(
    payload: CancelDeleteAccountRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.cancel_delete_account(payload=payload)




# ==============================================================================
"""
Change Password

request example
post {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "old_password": "old_password",
    "new_password": "new_password"
}

response example
{
    "success": true,
    "message": "Password changed successfully",
    "data": {}
}
"""
# ==============================================================================

@auth_router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    passwordService = PasswordService(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return passwordService.change_password(payload=payload)




# ==============================================================================
"""
Logout all sessions

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
    "message": "All sessions logged out successfully",
    "data": {}
"""
# ==============================================================================

@auth_router.post("/logout-all")
def logout_all(
    payload: LogoutAllRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    accountServices = AccountServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return accountServices.logout_all(payload=payload)


# ==============================================================================
"""
Link Google Account

request example
post {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "token_id": "token_id"
}

response example
{
    "success": true,
    "message": "Google account linked successfully",
    "data": {}
} 

"""
# ==============================================================================

@auth_router.post("/link-google")
def link_google(
    payload: LinkGoogleAccountRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    googleOauth = GoogleOauth()
    return googleOauth.link_google(
        payload=payload,
        request=request,
        background_tasks=background_tasks,
        db=db
    )




# ==============================================================================
# ==============================================================================
