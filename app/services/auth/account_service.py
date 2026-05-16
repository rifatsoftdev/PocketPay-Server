
from datetime import timedelta

from fastapi import BackgroundTasks, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.constants import AnsiColor, String, ENV
from app.enums import NotificationType
from app.model import DeletedUserTable, NotificationTable, SessionTable, SettingsTable, UserTable
from app.schema import (
    GlobalResponse, CancelDeleteAccountRequest, DeleteAccountRequest, LoginRequest,
    LogoutRequest, LogoutAllRequest, FCMTokenRequest, AccessTokenRequest
)
from app.utils import Hashing, Helpers, Token

from app.services.auth.user_verification import UserVerificationService
from app.services.auth.otp_service import OTPService

from app.services.auth.user_repository import UserRepository
from app.utils.notification_manager import NotificationManager
from app.services.auth.token_service import TokenGenerators



class AccountServices(OTPService, UserRepository, TokenGenerators):
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

    def login(
        self, 
        payload: LoginRequest
    ) -> GlobalResponse:
        try:
            email_address: str = payload.email_address
            phone_number: str = payload.phone_number
            country_code: str = payload.country_code
            user_password: str = payload.user_password
            device_id: str = payload.device_id
            device_uuid: str = payload.device_uuid

            for i, j in payload:
                print(f"{i} => {j}")
            
            # Request info
            ip: str = self.request.client.host
            user_agent: str = self.request.headers.get("user-agent")
            auth: str = self.request.headers.get("authorization"),
            path: str = self.request.url.path,
            query: dict = dict(self.request.query_params),
            cookies: dict = self.request.cookies
            
            # user login on phone number
            user: UserTable = self.check_user_already_exists(
                email=email_address,
                phone=phone_number,
                country_code=country_code
            )
            
            # user not found on database
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=String.USER_NOT_FOUND
                )

            settings: SettingsTable = user.settings

            if not settings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=String.SETTINGS_NOT_FOUND
                )

            if settings.account_locked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=String.ACCOUNT_LOCKED
                )

            if not user.password_hash:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=String.PASSWORD_NOT_SET
                )

            # check password
            if (not Hashing.verify_password(user_password, user.password_hash)):
                raise HTTPException(
                    status_code=401,
                    detail=String.INVALID_PASSWORD
                )

            access_token = None
            refresh_token = None

            is_2fa_required = bool(settings.two_factor_enabled)
            two_factor_methods = []

            if isinstance(settings.two_factor, dict):
                if settings.two_factor.get("totp"):
                    two_factor_methods.append("totp")
                if settings.two_factor.get("email"):
                    two_factor_methods.append("email")

            if not is_2fa_required:
                token_data = {
                    "user_id": user.user_id,
                    "email_address": user.email_address,
                    "device_id": device_id,
                    "device_uuid": device_uuid
                }

                access_token = self._create_token(
                    token_type="access",
                    expire_min=ENV.ACCESS_EXPIRE,
                    data=token_data
                )

                refresh_token = self._create_token(
                    token_type="refresh",
                    expire_min=ENV.REFRESH_EXPIRE,
                    data=token_data
                )
            
            # create a session
            session = SessionTable(
                user_id=user.user_id,
                fcm_token=None,
                access_token_hash=Hashing.create_hash(access_token) if access_token else None,
                refresh_token_hash=Hashing.create_hash(refresh_token) if refresh_token else None,
                device_uuid=device_uuid,
                device_id=device_id,
                login_at=Helpers.utc6dhaka(),
                last_ip_address=ip,
                is_login=not is_2fa_required,
                otp_verified=not is_2fa_required
            )
            self.db.add(session)

            # user Notification
            new_notification = NotificationTable(
                target_id=user.user_id,
                type=NotificationType.ALERT,
                title="New Login Detected",
                body=f"Your account was logged in from IP {ip} on {Helpers.utc6dhaka()}. If this wasn’t you, change your password immediately."
            )
            self.db.add(new_notification)

            # all commit and refresh
            self.db.commit()
            self.db.refresh(session)
            self.db.refresh(new_notification)

            if is_2fa_required:
                return GlobalResponse(
                    success=True,
                    message="Two-factor verification required",
                    data={
                        "requires_2fa": True,
                        "method": two_factor_methods[0] if two_factor_methods else None,
                        "methods": two_factor_methods,
                        "user_id": user.user_id,
                        "device_id": device_id,
                        "device_uuid": device_uuid
                    }
                )

            return GlobalResponse(
                success=True,
                message="Login successful",
                data={
                    "requires_2fa": False,
                    "user_id": user.user_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": ENV.ACCESS_EXPIRE,
                    "email_address": user.email_address,
                    "phone_number": f"{user.country_code or ''}{user.phone_number or ''}" or None
                }
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def logout(
        self, 
        payload: LogoutRequest
    ) -> GlobalResponse:
        try:
            # print(f"Logout attempt: {request}")
            user_id: str = payload.user_id
            access_token: str = payload.access_token
            device_id: str = payload.device_id
            device_uuid: str = payload.device_uuid

            user_verification_service = UserVerificationService(self.db)

            user = user_verification_service.verify_user(
                user_id=user_id,
                access_token=access_token,
                device_id=device_id,
                device_uuid=device_uuid
            )

            # Request info
            # ip:str = request.client.host
            # user_agent:str = request.headers.get("user-agent")
            # auth:str = request.headers.get("authorization"),
            # path:str = request.url.path,
            # query:dict = dict(request.query_params),
            # cookies:dict = request.cookies

            session = self.db.query(SessionTable).filter(
                SessionTable.user_id == user_id,
                SessionTable.device_id == device_id,
                SessionTable.device_uuid == device_uuid,
                SessionTable.is_login == True
            ).first()

            if not session:
                raise HTTPException(status_code=404, detail=String.SESSION_NOT_FOUND)
            
            session.is_login = False
            session.fcm_token = None
            session.logout_at = Helpers.utc6dhaka()
            
            self.db.commit()
            self.db.refresh(session)

            return GlobalResponse(
                success=True,
                message=String.LOGOUT_SUCCESSFUL,
                data={}
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def logout_all(self, payload: LogoutAllRequest):
        try:
            user_id: str = payload.user_id
            access_token: str = payload.access_token
            android_id: str = payload.device_id
            android_uuid: str = payload.device_uuid

            user_verification_service = UserVerificationService(
                db=self.db,
                background_tasks=self.background_tasks,
                request=self.request,
                authorization=self.authorization
            )

            user = user_verification_service.verify_user(
                user_id=user_id,
                access_token=access_token,
                android_id=android_id,
                android_uuid=android_uuid
            )

            sessions = self.db.query(SessionTable).filter(
                SessionTable.user_id == user_id,
                SessionTable.is_login == True
            ).all()

            for session in sessions:
                session.is_login = False
                session.fcm_token = None
                session.access_token_hash = None
                session.refresh_token_hash = None
                session.logout_at = Helpers.utc6dhaka()

            self.db.commit()

            return GlobalResponse(
                success=True,
                message="All sessions logged out successfully",
                data={}
            )

        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def get_new_access_token(self, payload: AccessTokenRequest) -> GlobalResponse:
        try:
            # get data
            refresh_token = payload.refresh_token
            user_id = payload.user_id
            android_id = payload.device_id
            android_uuid = payload.device_uuid

            session = self.db.query(SessionTable).filter(
                SessionTable.device_id == android_id,
                SessionTable.device_uuid == android_uuid
            ).first()

            if (not session):
                raise HTTPException(status_code=404, detail=String.SESSION_NOT_FOUND)

            if (not session.is_login or not session.otp_verified):
                raise HTTPException(status_code=401, detail=String.USER_NOT_LOGIN)

            payload = self._decode_token(refresh_token)

            # check token if expired payload is Null
            if payload == None:
                raise HTTPException(status_code=401, detail="Refresh token expired")
            
            # check token type
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token")

            access_token = self._create_token(
                expire_min=ENV.ACCESS_EXPIRE,
                data={
                    "user_id": payload.get("user_id"),
                    "email_address": payload.get("email_address"),
                    "android_id": payload.get("android_id"),
                    "android_uuid": payload.get("android_uuid")
                }
            )

            # update session
            session = self.db.query(SessionTable).filter(SessionTable.user_id == payload.get("user_id")).first()

            if session:
                session.access_token_hash = Hashing.create_hash(access_token)
                self.db.commit()
                self.db.refresh(session)

            return GlobalResponse(
                success=True,
                message="Access token refreshed successfully",
                data={
                    "access_token": access_token
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
    
    def receive_fcm_token(self, payload: FCMTokenRequest) -> GlobalResponse:
        try:
            # print(f"FCM token received: {request}")

            # get data
            user_id: str = payload.user_id
            access_token: str = payload.access_token
            android_id: str = payload.device_id
            android_uuid: str = payload.device_uuid
            fcm_token: str = payload.fcm_token
            
            # verify user
            user_verification_service = UserVerificationService(
                db=self.db,
                background_tasks=self.background_tasks,
                request=self.request,
                authorization=self.authorization
            )

            user = user_verification_service.verify_user(
                user_id=user_id,
                access_token=access_token,
                device_id=android_id,
                device_uuid=android_uuid
            )

            # find db
            existing = self.db.query(SessionTable).filter(
                SessionTable.user_id==user_id,
                SessionTable.device_id==android_id,
                SessionTable.device_uuid==android_uuid,
                SessionTable.is_login==True
            ).first()
            
            if existing:
                existing.fcm_token = fcm_token
                self.db.commit()
                self.db.refresh(existing)
            else:
                session = SessionTable(
                    user_id=user_id,
                    fcm_token=fcm_token
                )
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
            
            return GlobalResponse(
                success=True,
                message="FCM token received successfully",
                data={}
            )
        
        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def delete_account(self, payload: DeleteAccountRequest):
        try:
            user_id: str = payload.user_id
            access_token: str = payload.access_token
            android_id: str = payload.device_id
            android_uuid: str = payload.device_uuid
            user_password: str = payload.user_password
            reason: str = payload.reason

            # Request info
            ip: str = self.request.client.host

            user_verification_service = UserVerificationService(self.db)

            user = user_verification_service.verify_user(
                user_id=user_id,
                access_token=access_token,
                android_id=android_id,
                android_uuid=android_uuid
            )

            # check existing delete request
            existing_request = self.db.query(DeletedUserTable).filter(
                DeletedUserTable.user_id == user.user_id,
                DeletedUserTable.is_processed == False
            ).first()
            if existing_request:
                raise HTTPException(status_code=409, detail="Delete request already submitted")

            # schedule deletion (not immediate)
            scheduled_delete_at = Helpers.utc6dhaka() + timedelta(days=7)

            delete_record = DeletedUserTable(
                user_id=user.user_id,
                full_name=user.full_name,
                email_address=user.email_address,
                country_code=user.country_code,
                phone_number=user.phone_number,
                reason=reason,
                requested_at=Helpers.utc6dhaka(),
                scheduled_delete_at=scheduled_delete_at,
                is_processed=False
            )
            self.db.add(delete_record)

            # lock account to prevent further activity
            settings = self.db.query(SettingsTable).filter(SettingsTable.user_id == user.user_id).first()
            if settings:
                settings.account_locked = True

            # logout all sessions
            sessions = self.db.query(SessionTable).filter(
                SessionTable.user_id == user.user_id,
                SessionTable.is_login == True
            ).all()
            for session in sessions:
                session.is_login = False
                session.access_token_hash = None
                session.refresh_token_hash = None
                session.fcm_token = None
                session.logout_at = Helpers.utc6dhaka()

            # user Notification
            new_notification = NotificationTable(
                target_id=user.user_id,
                type=NotificationType.ALERT,
                title="Delete Account Requested",
                body=f"We received a delete account request from IP {ip}. Your account will be removed after review."
            )
            self.db.add(new_notification)

            # real time notification
            notifier = NotificationManager(self.db)
            notifier.send_user_notification(
                background_tasks=self.background_tasks,
                user_id=user.user_id,
                title="Delete Account Requested",
                short_body="We received your delete account request. Your account will be removed after review.",
                long_body=None,
                noty_type=NotificationType.ALERT,
                image_url=None,
                push=True,
                sms=False,
                email=False
            )

            self.db.commit()
            self.db.refresh(delete_record)
            self.db.refresh(new_notification)

            return GlobalResponse(
                success=True,
                message="Delete request submitted successfully",
                data={
                    "scheduled_delete_at": scheduled_delete_at
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def cancel_delete_account(self, payload: CancelDeleteAccountRequest) -> GlobalResponse:
        try:
            user_id: str = payload.user_id
            access_token: str = payload.access_token
            android_id: str = payload.device_id
            android_uuid: str = payload.device_uuid
            user_password: str = payload.user_password

            user_verification_service = UserVerificationService(self.db)

            user = user_verification_service.verify_user(
                user_id=user_id,
                access_token=access_token,
                android_id=android_id,
                android_uuid=android_uuid
            )

            delete_request = self.db.query(DeletedUserTable).filter(
                DeletedUserTable.user_id == user_id,
                DeletedUserTable.is_processed == False
            ).first()
            if not delete_request:
                raise HTTPException(status_code=404, detail="Delete request not found")

            self.db.delete(delete_request)

            settings = self.db.query(SettingsTable).filter(SettingsTable.user_id == user_id).first()
            if settings:
                settings.account_locked = False

            self.db.commit()

            return GlobalResponse(
                success=True,
                message="Delete request cancelled successfully",
                data={}
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)



