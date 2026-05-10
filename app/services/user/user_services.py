from fastapi import HTTPException, Header, Request, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.constants import AnsiColor, String
from app.schema import GlobalResponse
from app.model import SessionTable, UserTable
from app.utils import Helpers
from app.services.auth.user_verification import UserVerificationService

class UserServices:
    def __init__(
        self,
        db: Session,
        background_tasks: BackgroundTasks,
        request: Request,
        authorization: str
    ):
        self.db = db
        self.background_tasks = background_tasks
        self.request = request
        self.authorization = authorization

    @staticmethod
    def _format_date_of_birth(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value).split("T", 1)[0].split(" ", 1)[0]
    
    def get_profile(self):
        try:
            # print(f"Profile attempt: {request}")
            
            access_token = Helpers.authorization(self.authorization)

            # verify user
            user_verification_service = UserVerificationService(
                db=self.db,
                background_tasks=self.background_tasks,
                request=self.request,
                authorization=self.authorization
            )
            user_id = user_verification_service.verify_access_token(
                access_token=access_token
            )

            user = self.db.query(UserTable).filter(
                UserTable.user_id == user_id
            ).first()

            settings = user.settings

            # get session detals
            session = self.db.query(SessionTable).filter(SessionTable.user_id == user.user_id).first()

            return GlobalResponse(
                success=True,
                message="Profile fetched successfully",
                data={
                    "profile": {
                        "user_id": user.user_id,
                        "full_name": user.full_name,
                        "email_address": user.email_address,
                        "phone_number": f"{user.country_code or ''}{user.phone_number or ''}",
                        "country_code": user.country_code,
                        "gender": user.user_gender,
                        "date_of_birth": self._format_date_of_birth(user.date_of_birth),
                        "phone_verified": user.phone_verified,
                        "email_verified": user.email_verified,
                        "link_google": user.link_google,
                        "profile_picture": user.profile_image_url,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    },
                    "settings": {
                        "allow_notifications": settings.allow_notifications if settings else None,
                        "dark_mode": settings.dark_mode if settings else None,
                        "country": settings.country if settings else None,
                        "language": settings.language if settings else None,

                        "totp_enabled": settings.two_factor_enabled if settings else None,
                        "biometric_enabled": settings.biometric_enabled if settings else None,
                        "account_locked": settings.account_locked if settings else None,

                        "kyc_status": settings.kyc_status if settings else None,
                        "kyc_verified_by": settings.kyc_verified_by if settings else None,
                        "kyc_verified_at": settings.kyc_verified_at.isoformat() if settings and settings.kyc_verified_at else None
                    },
                    "session": {
                        "device_type": session.device_type if session else None,
                        "device_name": session.device_name if session else None,
                        "last_ip_address": session.last_ip_address if session else None,
                        "login_at": session.login_at.isoformat() if session and session.login_at else None
                    }
                }
            )
        
        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def edit_info(self):
        try:
            # print(f"Profile attempt: {request}")
            
            access_token = Helpers.authorization(self.authorization)

            # verify user
            user_verification_service = UserVerificationService(
                db=self.db,
                background_tasks=self.background_tasks,
                request=self.request,
                authorization=self.authorization
            )
            user_id = user_verification_service.verify_access_token(
                access_token=access_token
            )

            user = self.db.query(UserTable).filter(
                UserTable.user_id == user_id
            ).first()

            return GlobalResponse(
                success=True,
                message="Profile Edit Info",
                data={
                    "full_name": user.full_name,
                    "gender": user.user_gender,
                    "date_of_birth": self._format_date_of_birth(user.date_of_birth),
                    "profile_picture": user.profile_image_url
                }
            )
        
        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
    
    
