from fastapi import HTTPException, BackgroundTasks, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.constants import AnsiColor, ENV, String
from app.utils import Generators, Hashing
from app.enums import KYCStatus, NotificationType
from app.model import UserTable, SettingsTable, SessionTable, WalletTable, NotificationTable
from app.schema.auth_schemas import RegisterRequest
from app.schema.global_schema import GlobalResponse
from app.services.auth.user_repository import UserRepository

from app.utils.reward_service import RewardService
from app.utils.notification_manager import NotificationManager
from app.utils.bg_task import send_welcome_email


class RegistrationService(UserRepository):
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
    
    def __create_new_user(
        self,
        full_name: str,
        email_address: str,
        phone_number: str,
        country_code: str,
        user_password: str,
        profile_image_url: str,
        device_id: str,
        device_uuid: str,
        ip: str
    ) -> UserTable:
        user_id = Generators.generate_id("user")

        new_user = UserTable(
            user_id=user_id,
            full_name=full_name,
            email_address=email_address,
            phone_number=phone_number,
            country_code=country_code,
            password_hash=Hashing.create_hash(user_password) if user_password else None,
            profile_image_url=profile_image_url
        )
        self.db.add(new_user)
        self.db.flush()
        

        # Create wallet for new user
        wallet = WalletTable(
            user_id=user_id,
            balance=0,
            # currency=country_code_to_currency(newUserCountryCode),
            last_updated=datetime.now(timezone.utc)
        )
        self.db.add(wallet)
        self.db.flush()
        

        # create settings
        settings = SettingsTable(
            user_id=user_id,
            allow_notifications=True,
            dark_mode=False,
            language="en",
            account_locked=False,
            kyc_status=KYCStatus.PENDING,
            kyc_verified_at=None
        )
        self.db.add(settings)
        self.db.flush()
    
        # create session
        session = SessionTable(
            user_id=user_id,
            fcm_token=None,
            access_token_hash=None,
            refresh_token_hash=None,
            device_uuid=device_uuid,
            device_id=device_id,
            last_ip_address=ip
        )
        self.db.add(session)
        self.db.flush()

        return new_user

    def new_user(
        self,
        full_name: str,
        email_address: str,
        device_id: str,
        device_uuid: str,
        ip: str,
        background_tasks: BackgroundTasks,
        phone_number: str = None,
        country_code: str = None,
        user_password: str = None,
        profile_image_url: str = None,
    )-> UserTable | None:
        """Create a new user."""
        try:
            if self.check_user_already_exists(
                email=email_address,
                phone=phone_number,
                country_code=country_code
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=String.USER_ALRADY_EXISTS
                )

            created_user = self.__create_new_user(
                full_name=full_name,
                email_address=email_address,
                phone_number=phone_number,
                country_code=country_code,
                user_password=user_password,
                profile_image_url=profile_image_url,
                device_id=device_id,
                device_uuid=device_uuid,
                ip=ip
            )
            
            # user Notification
            new_notification = NotificationTable(
                target_id=created_user.user_id,
                type=NotificationType.ALERT,
                title="Welcome to PocketPay! 🔐",
                body=f"Your account has been successfully set up. Your security is our priority—let’s get started."
            )
            self.db.add(new_notification)
            self.db.flush()

            # sent welcome email
            background_tasks.add_task(send_welcome_email, email_address)

            # real time notification
            notifier = NotificationManager(self.db)

            notifier.send_user_notification(
                background_tasks=background_tasks,
                user_id=created_user.user_id,
                title="Welcome to PocketPay! 🔐",
                short_body=f"Your account has been successfully set up. Your security is our priority—let’s get started.",
                long_body=None,
                noty_type=NotificationType.ALERT,
                image_url=None,
                push=True,
                sms=False,
                email=False
            )

            # db commit and refresh
            self.db.commit()
            self.db.refresh(created_user)
            # db.refresh(wallet)
            # db.refresh(settings)
            # db.refresh(session)
            self.db.refresh(new_notification)

            # return new user
            return created_user

        
        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def register(
        self,
        payload: RegisterRequest
    ) -> GlobalResponse:
        """Register a user and apply referral/welcome rewards."""
        try:
            ip: str = self.request.client.host

            created_user = self.new_user(
                full_name=payload.full_name,
                email_address=payload.email_address,
                phone_number=payload.phone_number,
                country_code=payload.country_code,
                user_password=payload.user_password,
                profile_image_url=String.DEMO_PROFILE_IMAGE_URL,
                device_id=payload.device_id,
                device_uuid=payload.device_uuid,
                ip=ip,
                background_tasks=self.background_tasks
            )

            reward_service = RewardService()
            referral_user = None

            if payload.referral_account:
                referral_user = self.db.query(UserTable).filter(
                    UserTable.email_address == payload.referral_account
                ).first()

                if referral_user:
                    reward_service.send_reward(
                        background_tasks=self.background_tasks,
                        db=self.db,
                        user_id=referral_user.user_id,
                        title="Referral Reward",
                        body=f"Your referral {payload.email_address} was successfuly registered. You have rechived a reward of {ENV.USER_REFERRAL_REWARD} BD.",
                        amount=ENV.USER_REFERRAL_REWARD
                    )

            reward_amount = (
                ENV.NEW_USER_REWARD_WITH_REFERRAL
                if referral_user
                else ENV.NEW_USER_REWARD_WITH_NO_REFERRAL
            )

            reward_service.send_reward(
                background_tasks=self.background_tasks,
                db=self.db,
                user_id=created_user.user_id,
                title="Welcome Reward",
                body=f"Welcome to PocketPay! You have rechived a reward of {reward_amount} BD.",
                amount=reward_amount
            )

            self.db.commit()
            self.db.refresh(created_user)

            return GlobalResponse(
                success=True,
                message="Registration successful. Please verify with the OTP sent to your phone.",
                data={"sent_otp": False}
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
