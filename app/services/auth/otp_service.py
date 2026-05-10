from fastapi import HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone

from app.constants import ENV, AnsiColor, String
from app.model import OTPTable, SessionTable, UserTable
from app.schema import OTPRequest, GlobalResponse
from app.schema.auth_schemas import VerifyOTPRequest
from app.utils import Token, Generators, Hashing, Helpers
from app.utils.bg_task import send_otp_email


class OTPService:
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

    def send_otp(
        self,
        payload: OTPRequest
    ) -> GlobalResponse:
        try:
            # print(f"{AnsiColor.BLUE}INFO{AnsiColor.RESET}:     {request}")
            # get request data 
            method = payload.method
            delever_to = payload.delever_to
            device_id = payload.device_id
            device_uuid = payload.device_uuid

            # Request info
            # ip:str = request.client.host
            # user_agent:str = request.headers.get("user-agent")
            # auth:str = request.headers.get("authorization"),
            # path:str = request.url.path,
            # query:dict = dict(request.query_params),
            # cookies:dict = request.cookies

            # check
            if not delever_to:
                raise HTTPException(status_code=400, detail="Email or phone required to send OTP")

            # check otp record
            otp_record = self.db.query(OTPTable).filter(
                OTPTable.delever_to == delever_to
            ).first()

            # delete old otp if exist
            if otp_record:
                self.db.delete(otp_record)
                self.db.commit()
            
            # genatet otp token
            token_service = Token()
            otp_token = token_service.create_otp_token(data={
                "method": method,
                "delever_to": delever_to,
                "device_id": device_id,
                "device_uuid": device_uuid
            })

            # genaret OTP
            make_otp = Generators.generate_otp()
            otp_hash = Hashing.create_hash(make_otp)

            # insert otp data
            otp_record = OTPTable(
                user_id=None,
                otp_token=otp_token,
                device_id=device_id,
                device_uuid=device_uuid,
                delever_to=delever_to,
                otp_hash=otp_hash,
                expires_at=Helpers.utc6dhaka() + timedelta(minutes=5)
            )
            self.db.add(otp_record)

            if (ENV.DEBUG):
                print(f"{AnsiColor.BLUE}INFO{AnsiColor.RESET}:     OTP sent to {delever_to} code {make_otp}")

            # send OTP on user
            if (method == "email"):
                self.background_tasks.add_task(send_otp_email, delever_to, make_otp)
                status = True
            elif (method == "phone"):
                otp_manager = SMSSent()
                status = otp_manager.send_sms(
                    to_phone=delever_to,
                    title="",
                    body=f"Your OTP code is {make_otp}. Please use this code to complete your verification."
                )

            # check otp send status
            if not status:
                raise HTTPException(status_code=500, detail="Failed to send OTP")

            self.db.commit()
            self.db.refresh(otp_record)

            return GlobalResponse(
                success=True,
                message="OTP resent successfully",
                data={
                    "otp_token": otp_token
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def verify_otp(
        self,
        payload: VerifyOTPRequest
    ) -> GlobalResponse:
        try:
            method: str = payload.method
            deliver_to: str = payload.delever_to
            otp: str = payload.otp
            otp_token: str = payload.otp_token
            device_id: str = payload.device_id
            device_uuid: str = payload.device_uuid

            ip: str = self.request.client.host

            otp_record = self.db.query(OTPTable).filter(
                OTPTable.delever_to == deliver_to,
                OTPTable.otp_token == otp_token
            ).first()

            if not otp_record:
                raise HTTPException(status_code=404, detail=String.OTP_NOT_FOUND)

            token_service = Token()
            token_payload = token_service.decode_token(otp_token)

            if token_payload is None:
                raise HTTPException(status_code=401, detail=String.TIME_LIMET_EXPAIRE)

            token_device_id = token_payload.get("device_id") or token_payload.get("android_id")
            token_device_uuid = token_payload.get("device_uuid") or token_payload.get("android_uuid")
            if device_id != token_device_id or device_uuid != token_device_uuid:
                raise HTTPException(status_code=401, detail="Invalid Device")

            if not Hashing.verify_otp(otp, otp_record.otp_hash):
                raise HTTPException(status_code=401, detail=String.INVALID_OTP)

            user = self.db.query(UserTable).filter(
                or_(
                    UserTable.email_address == deliver_to,
                    UserTable.phone_number == deliver_to[3::]
                )
            ).first()

            if not user:
                raise HTTPException(status_code=404, detail=String.USER_NOT_FOUND)

            self.db.delete(otp_record)

            if not user.email_verified and method == "email":
                user.email_verified = True

            if not user.phone_verified and method == "phone":
                user.phone_verified = True

            self.db.commit()

            access_token = token_service.create_access_token(data={
                "user_id": user.user_id,
                "email_address": user.email_address,
                "device_id": device_id,
                "device_uuid": device_uuid
            })

            refresh_token = token_service.create_refresh_token(data={
                "user_id": user.user_id,
                "email_address": user.email_address,
                "device_id": device_id,
                "device_uuid": device_uuid
            })

            session = self.db.query(SessionTable).filter(
                SessionTable.user_id == user.user_id,
                SessionTable.device_id == device_id,
                SessionTable.device_uuid == device_uuid,
                SessionTable.refresh_token_hash == None,
                SessionTable.is_login == False
            ).first()

            if session:
                session.access_token_hash = Hashing.create_hash(access_token)
                session.refresh_token_hash = Hashing.create_hash(refresh_token)
                session.last_ip_address = ip
                session.is_login = True
                session.otp_verified = True
                session.login_at = Helpers.utc6dhaka()
                self.db.commit()
                self.db.refresh(session)
            else:
                session = SessionTable(
                    user_id=user.user_id,
                    fcm_token=None,
                    access_token_hash=Hashing.create_hash(access_token),
                    refresh_token_hash=Hashing.create_hash(refresh_token),
                    device_uuid=device_uuid,
                    device_id=device_id,
                    last_ip_address=ip,
                    is_login=True,
                    otp_verified=True,
                )
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)

            return GlobalResponse(
                success=True,
                message="OTP verified successfully",
                data={
                    "user_id": user.user_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": 900,
                    "email_address": user.email_address,
                    "phone_number": user.country_code + user.phone_number
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    
