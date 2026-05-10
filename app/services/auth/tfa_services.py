from fastapi import HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from datetime import timedelta

from app.constants import AnsiColor, ENV, String
from app.model import OTPTable, SettingsTable
from app.schema import (
    GlobalResponse, TOTPSetupRequest, TOTPConfirmRequest, TOTPAuthDisableRequest,
    EmailTFASetupRequest, EmailTFAConfirmRequest, EmailTFADisableRequest
)
from app.services.auth.user_verification import UserVerificationService
from app.utils import Generators, Hashing, Helpers, Token, TwoFactorAuth
from app.utils.bg_task import send_otp_email


class TFAServices:
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

    def __verify_user(self, user_id: str, access_token: str, device_id: str, device_uuid: str, password: str = None):
        user_verification_service = UserVerificationService(
            db=self.db,
            background_tasks=self.background_tasks,
            request=self.request,
            authorization=self.authorization
        )

        return user_verification_service.verify_user(
            user_id=user_id,
            access_token=access_token,
            device_id=device_id,
            device_uuid=device_uuid,
            password=password,
            advance_check=False
        )

    def __get_settings(self, user_id: str) -> SettingsTable:
        settings = self.db.query(SettingsTable).filter(SettingsTable.user_id == user_id).first()
        if not settings:
            raise HTTPException(status_code=404, detail=String.SETTINGS_NOT_FOUND)

        return settings

    @staticmethod
    def __two_factor_data(settings: SettingsTable) -> dict:
        if isinstance(settings.two_factor, dict):
            return dict(settings.two_factor)

        return {}

    @staticmethod
    def __totp_secret(settings: SettingsTable) -> str:
        two_factor = TFAServices.__two_factor_data(settings)
        return two_factor.get("totp") or two_factor.get("secret")

    @staticmethod
    def __email_tfa(settings: SettingsTable) -> str:
        two_factor = TFAServices.__two_factor_data(settings)
        return two_factor.get("email")

    @staticmethod
    def __has_tfa_method(two_factor: dict) -> bool:
        return bool(two_factor.get("totp") or two_factor.get("email"))

    @staticmethod
    def __device_id(payload) -> str:
        return getattr(payload, "device_id", None) or getattr(payload, "android_id", None)

    @staticmethod
    def __device_uuid(payload) -> str:
        return getattr(payload, "device_uuid", None) or getattr(payload, "android_uuid", None)

    def totp_setup(self, payload: TOTPSetupRequest) -> GlobalResponse:
        try:
            user = self.__verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=self.__device_id(payload),
                device_uuid=self.__device_uuid(payload)
            )

            settings = self.__get_settings(user.user_id)

            if settings.two_factor_enabled and self.__totp_secret(settings):
                raise HTTPException(status_code=400, detail="Two Factor Authentication already enabled")

            secret = TwoFactorAuth.generate_secret()
            settings.two_factor = {
                **self.__two_factor_data(settings),
                "totp": secret
            }
            settings.two_factor_enabled = False

            qr_uri = TwoFactorAuth.get_qr_uri(
                user_email=user.email_address,
                issuer="PocketPay",
                secret=secret
            )

            self.db.commit()
            self.db.refresh(settings)

            return GlobalResponse(
                success=True,
                message="TOTP secret generated",
                data={
                    "totp_secret": secret,
                    "qr_uri": qr_uri
                }
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def totp_confirm(self, payload: TOTPConfirmRequest) -> GlobalResponse:
        try:
            user = self.__verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=self.__device_id(payload),
                device_uuid=self.__device_uuid(payload)
            )

            settings = self.__get_settings(user.user_id)
            stored_secret = self.__totp_secret(settings)

            if not stored_secret:
                raise HTTPException(status_code=400, detail="TOTP secret not found")

            if not TwoFactorAuth.verify_otp(stored_secret, payload.totp_code):
                raise HTTPException(status_code=400, detail="Invalid TOTP code")

            settings.two_factor = {
                **self.__two_factor_data(settings),
                "totp": stored_secret
            }
            settings.two_factor_enabled = True

            self.db.commit()
            self.db.refresh(settings)

            return GlobalResponse(
                success=True,
                message="Two Factor Authentication enabled",
                data={}
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def totp_disable(self, payload: TOTPAuthDisableRequest) -> GlobalResponse:
        try:
            user = self.__verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=self.__device_id(payload),
                device_uuid=self.__device_uuid(payload),
                password=payload.user_password
            )

            settings = self.__get_settings(user.user_id)

            if not settings.two_factor_enabled:
                raise HTTPException(status_code=400, detail="Two Factor Authentication is already disabled")

            if not self.__totp_secret(settings):
                raise HTTPException(status_code=400, detail="TOTP secret not found")

            two_factor = self.__two_factor_data(settings)
            two_factor.pop("totp", None)
            two_factor.pop("secret", None)

            settings.two_factor = two_factor or None
            settings.two_factor_enabled = self.__has_tfa_method(two_factor)

            self.db.commit()
            self.db.refresh(settings)

            return GlobalResponse(
                success=True,
                message="Two Factor Authentication disabled",
                data={}
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def email_setup(self, payload: EmailTFASetupRequest) -> GlobalResponse:
        try:
            user = self.__verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=self.__device_id(payload),
                device_uuid=self.__device_uuid(payload)
            )

            settings = self.__get_settings(user.user_id)
            if settings.two_factor_enabled and self.__email_tfa(settings):
                raise HTTPException(status_code=400, detail="Email Two Factor Authentication already enabled")

            old_otp = self.db.query(OTPTable).filter(
                OTPTable.user_id == user.user_id,
                OTPTable.delever_to == user.email_address
            ).first()
            if old_otp:
                self.db.delete(old_otp)
                self.db.flush()

            token_service = Token()
            otp_token = token_service.create_otp_token(data={
                "method": "email_tfa",
                "user_id": user.user_id,
                "delever_to": user.email_address,
                "device_id": self.__device_id(payload),
                "device_uuid": self.__device_uuid(payload)
            })

            otp = Generators.generate_otp()
            otp_record = OTPTable(
                user_id=user.user_id,
                otp_token=otp_token,
                device_id=self.__device_id(payload),
                device_uuid=self.__device_uuid(payload),
                delever_to=user.email_address,
                otp_hash=Hashing.create_hash(otp),
                expires_at=Helpers.utc6dhaka() + timedelta(minutes=5)
            )
            self.db.add(otp_record)

            if ENV.DEBUG:
                print(f"{AnsiColor.BLUE}INFO{AnsiColor.RESET}:     Email TFA OTP sent to {user.email_address} code {otp}")

            self.background_tasks.add_task(send_otp_email, user.email_address, otp)

            self.db.commit()
            self.db.refresh(otp_record)

            return GlobalResponse(
                success=True,
                message="Email TFA code sent",
                data={
                    "otp_token": otp_token,
                    "email": user.email_address
                }
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def email_confirm(self, payload: EmailTFAConfirmRequest) -> GlobalResponse:
        try:
            user = self.__verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=self.__device_id(payload),
                device_uuid=self.__device_uuid(payload)
            )

            settings = self.__get_settings(user.user_id)

            otp_record = self.db.query(OTPTable).filter(
                OTPTable.user_id == user.user_id,
                OTPTable.delever_to == user.email_address,
                OTPTable.otp_token == payload.otp_token
            ).first()

            if not otp_record:
                raise HTTPException(status_code=404, detail=String.OTP_NOT_FOUND)

            token_payload = Token().decode_token(payload.otp_token)
            if token_payload is None:
                raise HTTPException(status_code=401, detail=String.TIME_LIMET_EXPAIRE)

            if token_payload.get("method") != "email_tfa":
                raise HTTPException(status_code=401, detail=String.INVALID_TOKEN_TYPE)

            if token_payload.get("user_id") != user.user_id:
                raise HTTPException(status_code=401, detail=String.INVALID_TOKEN)

            token_device_id = token_payload.get("device_id") or token_payload.get("android_id")
            token_device_uuid = token_payload.get("device_uuid") or token_payload.get("android_uuid")
            if self.__device_id(payload) != token_device_id or self.__device_uuid(payload) != token_device_uuid:
                raise HTTPException(status_code=401, detail="Invalid Device")

            if not Hashing.verify_otp(payload.otp, otp_record.otp_hash):
                raise HTTPException(status_code=401, detail=String.INVALID_OTP)

            two_factor = self.__two_factor_data(settings)
            settings.two_factor = {
                **two_factor,
                "email": user.email_address
            }
            settings.two_factor_enabled = True
            self.db.delete(otp_record)

            self.db.commit()
            self.db.refresh(settings)

            return GlobalResponse(
                success=True,
                message="Email Two Factor Authentication enabled",
                data={}
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def email_disable(self, payload: EmailTFADisableRequest) -> GlobalResponse:
        try:
            user = self.__verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=self.__device_id(payload),
                device_uuid=self.__device_uuid(payload),
                password=payload.user_password
            )

            settings = self.__get_settings(user.user_id)
            if not self.__email_tfa(settings):
                raise HTTPException(status_code=400, detail="Email Two Factor Authentication is already disabled")

            two_factor = self.__two_factor_data(settings)
            two_factor.pop("email", None)

            settings.two_factor = two_factor or None
            settings.two_factor_enabled = self.__has_tfa_method(two_factor)

            self.db.commit()
            self.db.refresh(settings)

            return GlobalResponse(
                success=True,
                message="Email Two Factor Authentication disabled",
                data={}
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
