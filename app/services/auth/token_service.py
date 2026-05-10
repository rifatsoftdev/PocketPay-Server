from fastapi import HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt

from app.constants import ENV, String, AnsiColor
from app.schema import AccessTokenRequest, GlobalResponse, FCMTokenRequest
from app.model import SessionTable
from app.utils import Hashing

from app.services.auth.user_verification import UserVerificationService


class TokenGenerators:
    def __init__(self, db: Session):
        self.SECRET_KEY = ENV.SECRET_KEY
        self.ALGORITHM = ENV.ALGORITHM

    def _create_token(
        self,
        data: dict,
        token_type: str = "access",
        expire_day: float = 0,
        expire_min: float = 0
    ) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=expire_day, minutes=expire_min)
        to_encode.update({
            "exp": expire,
            "type": token_type
        })
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        
    def _decode_token(self, token: str):
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    

class TokenService(TokenGenerators):
    def __init__(
        self,
        db: Session,
        background_tasks: BackgroundTasks,
        request: Request,
        authorization: str
    ):
        super().__init__(db)
        self.db = db
        self.background_tasks = background_tasks
        self.request = request
        self.authorization = authorization

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

    
