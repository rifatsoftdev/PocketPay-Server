from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Header, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from datetime import date
import traceback

from app.core.database import get_db

from app.constants import AnsiColor, String, ENV
from app.model import SessionTable
from app.schema import TOTPVerifyRequest, TOTPDisableRequest, GlobalResponse, GlobalRequest
from app.services import UserServices, TFAServices
from app.services.auth.user_verification import UserVerificationService
from app.utils import CloudinaryStorage, Helpers





user_router = APIRouter()

# Cloudinary Storage init
cloudinaryStorage = CloudinaryStorage(
    ENV.CLOUDINARY_CLOUD_NAME,
    ENV.CLOUDINARY_API_KEY,
    ENV.CLOUDINARY_API_SECRET
)

ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
MAX_SIZE = 5 * 1024 * 1024  # 5MB


# ==============================================================================
"""
get user data

request example
post {
    "user_id": "89eb4658-a1a6-40d2-845a-835f5d8a14e3",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiODllYjQ2NTgtYTFhNi00MGQyLTg0NWEtODM1ZjVkOGExNGUzIiwiZW1haWwiOiJkYXZpZEBnbWFpbC5jb20iLCJhbmRyb2lkX2lkIjoiYW5kcm9pZF9pZCIsInV1aWQiOiJ1dWlkIiwiZXhwIjoxNzcyNDI5MzgwLCJ0eXBlIjoiYWNjZXNzIn0.Kf6fxZ69mcJxQUOVUdZNZiS5wzmBvpdsjLIBgzt-sVs",
    "android_id": "android_id",
    "android_uuid": "android_uuid"
}

response example
{
    "success": true,
    "message": "Profile fetched successfully",
    "data": {
        "profile": {
            "user_id": "89eb4658-a1a6-40d2-845a-835f5d8a14e3",
            "full_name": "David",
            "email_address": "david@gmail.com",
            "phone_number": "+8801812345677",
            "country_code": "+88",
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "phone_verified": false,
            "email_verified": true,
            "link_google": false,
            "profile_picture": null,
            "created_at": "2026-01-31T05:25:08"
        },
        "settings": {
            "allow_notifications": true,
            "dark_mode": false,
            "country": "BD",
            "language": "en",

            "totp_enabled": false,
            "biometric_enabled": false,
            "account_locked": false,

            "kyc_status": "pending",
            "kyc_verified_by": null,
            "kyc_verified_at": null
        },
        "session": {
            "device_type": null,
            "device_name": null,
            "last_ip_address": "192.168.1.100",
            "login_at": "2026-01-31T05:29:41.048411"
        }
    }
}
"""
# ==============================================================================

@user_router.get("/profile", response_model=GlobalResponse)
async def get_profile(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    userServices = UserServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return userServices.get_profile()
    



@user_router.get("/edit-info", response_model=GlobalResponse)
async def edit_info(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    userServices = UserServices(
        db=db,
        background_tasks=background_tasks,
        request=request,
        authorization=authorization
    )

    return userServices.edit_info()




# ==============================================================================
"""
update user profile

request example
patch {
    "user_id": "user_id",
    "access_token": "access_token",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "full_name": "David",
    "gender": "male",
    "date_of_birth": "1990-01-01",
    "avatar": "Image File"
}

response example
{
    "success": true,
    "message": "Profile updated successfully",
    "data": {}
}

"""
# ==============================================================================

@user_router.post("/profile/update")
async def update_profile(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Form(...),
    access_token: str = Form(...),
    device_id: str = Form(...),
    device_uuid: str = Form(...),

    full_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    date_of_birth: Optional[date] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        print(
            f"{AnsiColor.BLUE}INFO{AnsiColor.RESET}: /profile/update content-type="
            f"{request.headers.get('content-type')}"
        )

        # verify user
        user_verification_service = UserVerificationService(db)
        user = user_verification_service.verify_user(
            user_id=user_id,
            access_token=access_token,
            device_id=device_id,
            device_uuid=device_uuid,
            password=None,
            advance_check=False
        )

        if full_name is not None:
            user.full_name = full_name

        if gender is not None:
            normalized_gender = gender.strip().lower()
            if normalized_gender not in ["male", "female", "other", "undefined"]:
                raise HTTPException(status_code=400, detail="Invalid gender value")
            user.user_gender = normalized_gender

        if date_of_birth is not None:
            user.date_of_birth = date_of_birth

        upload_file = avatar or photo or file
        upload_field = "avatar" if avatar else ("photo" if photo else ("file" if file else None))

        if upload_file is not None:
            if upload_file.content_type and upload_file.content_type not in ALLOWED_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail="Only JPG, PNG, WEBP images allowed"
                )

            upload_file.file.seek(0, 2)
            size = upload_file.file.tell()
            upload_file.file.seek(0)

            if size > MAX_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail="Image size must be under 5MB"
                )

            try:
                upload_result = cloudinaryStorage.upload_file(
                    file_path=upload_file.file,
                    public_id=f"{user.user_id}/{upload_field}",
                    file_type="image"
                )
                print(
                    f"{AnsiColor.BLUE}INFO{AnsiColor.RESET}: cloudinary upload success "
                    f"secure_url={upload_result.get('secure_url')}"
                )
            except Exception as upload_error:
                print(f"{AnsiColor.RED}ERROR{AnsiColor.RESET}: Cloudinary upload failed -> {upload_error}")
                traceback.print_exc()
                raise HTTPException(
                    status_code=502,
                    detail=f"Cloudinary upload failed: {str(upload_error)}"
                )

            user.profile_image_url = upload_result.get("secure_url")
            if not user.profile_image_url:
                raise HTTPException(status_code=502, detail="Cloudinary upload failed: secure_url missing")
        else:
            print(
                f"{AnsiColor.YELLOW}INFO{AnsiColor.RESET}: no file received in form-data. "
                "Use one file key: avatar/photo/file"
            )

        db.commit()
        db.refresh(user)

        return GlobalResponse(
            success=True,
            message="Profile updated successfully",
            data={
                "profile_picture": user.profile_image_url
            }
        )
    
    except HTTPException:
        raise

    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=String.SERVER_ERROR)





# ==============================================================================
"""
Uplode image

request example
post 
"""
# ==============================================================================

@user_router.post("/image-upload")
async def upload_image(file: UploadFile = File(...)):
    # type check
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, WEBP images allowed"
        )

    # size check
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image size must be under 5MB"
        )

    try:
        result = cloudinaryStorage.upload_file(
            file_path=file.file,
            public_id=f"{file.filename}",
            file_type="image"
        )

        return GlobalResponse(
            success=True,
            message="Image uploaded successfully",
            data={
                "img_url": result["secure_url"],
            }
        )

    except Exception as e:
        print(f"{AnsiColor.RED}ERROR{AnsiColor.RESET}:     {e}")
        raise HTTPException(status_code=500, detail=String.SERVER_ERROR)







# ==============================================================================
"""
Two Fector Request

request example 
post {
    "user_id": "user_id",
    "android_id": "android_id",
    "android_uuid": "android_uuid",
    "access_token": "access_token".
    "secret": "secret",
    "totp_code": "totp_code"
}

response example
{
    "success": true,
    "message": "TOTP secret generated",
    "data": {
        "totp_secret": "secret",
        "qr_uri": "qr_uri"
    }
}
"""
# ==============================================================================

# @user_router.post("/2fa/enable")
# async def totp_enable(
#     payload: TOTPVerifyRequest,
#     request: Request,
#     background_tasks: BackgroundTasks,
#     authorization: str = Header(None),
#     db: Session = Depends(get_db)
# ):
#     tfaService = TFAServices(
#         db=db,
#         background_tasks=background_tasks,
#         request=request,
#         authorization=authorization
#     )

#     return tfaService.totp_confirm(payload=payload)






# ==============================================================================
"""
Disable Two Factor Authentication
"""
# ==============================================================================

# @user_router.post("/2fa/disable")
# async def totp_disable(
#     payload: TOTPDisableRequest,
#     request: Request,
#     background_tasks: BackgroundTasks,
#     authorization: str = Header(None),
#     db: Session = Depends(get_db)
# ):
#     tfaService = TFAServices(
#         db=db,
#         background_tasks=background_tasks,
#         request=request,
#         authorization=authorization
#     )

#     return tfaService.totp_disable(payload=payload)





# kyc/submit
# ==============================================================================
# ==============================================================================
