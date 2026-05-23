import smtplib, json
import firebase_admin

from enum import Enum
from firebase_admin import credentials, messaging
from firebase_admin._messaging_utils import UnregisteredError
from firebase_admin.exceptions import FirebaseError
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from email.mime.text import MIMEText

from app.constants import AnsiColor, ENV
from app.model import UserTable, SessionTable

from app.router.notify_router import check_online_user, send_notification as send_ws_notification


class NotificationData:
    def __init__(
        self,
        user_id: str,
        title: str,
        body: str = None,
        noty_type: str = "default",
        data: dict = None,
        image_url: str = None,
        priority: str = "normal",
        short_body: str = None,
        push: bool = True,
        email: bool = True,
        sms: bool = True
    ):
        self.user_id = user_id
        self.title = title
        self.body = body or short_body or ""
        self.noty_type = self._stringify(noty_type)
        self.data = data or {}
        self.image_url = image_url
        self.priority = priority
        self.push = push
        self.email = email
        self.sms = sms

    @staticmethod
    def _stringify(value) -> str:
        if value is None:
            return ""
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)


class NotificationServices:
    def __init__(self, db: Session, background_tasks: BackgroundTasks):
        self.db = db
        self.background_tasks = background_tasks
        
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred_dict = json.loads(ENV.POCKETPAY_ADMINSDK)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        

    def send_by_push(self, fcm_token: str, data: NotificationData) -> bool:
        """
        Single device token এ push notification send
        Returns True if successful, False if failed
        """
        try:
            payload = {
                "type": data.noty_type,
                "noty_type": data.noty_type,
                "title": data.title,
                "body": data.body,
                "img_url": data.image_url or "",
                **data.data
            }

            message = messaging.Message(
                notification=messaging.Notification(
                    title=data.title,
                    body=data.body,
                    image=data.image_url
                ),
                data={key: NotificationData._stringify(value) for key, value in payload.items()},
                token=fcm_token
            )
            response = messaging.send(message)
            return True if response else False
        
        except UnregisteredError:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     Device unregistered!")
            return False
        
        except FirebaseError as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            return False
        
        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            return False


    def send_by_email(self, to_email: str, data: NotificationData) -> bool:
        email_address = ENV.EMAIL_ADDRESS
        email_password = ENV.EMAIL_PASSWORD
        smtp_server = ENV.SMTP_SERVER
        smtp_port = ENV.SMTP_PORT

        msg = MIMEText(data.body, 'html')
        msg['Subject'] = data.title
        msg['From'] = email_address
        msg['To'] = to_email

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_address, email_password)
                server.sendmail(email_address, to_email, msg.as_string())
            return True
        
        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            return False


    def send_by_sms(self, phone_number: str, data: NotificationData) -> bool:
        # Placeholder for SMS gateway integration
        print(f"{AnsiColor.GREEN}SMS SENT{AnsiColor.RESET} to {phone_number}: {data.title} - {data.body}")
        return True

    
    def send_notification(self, data: NotificationData) -> bool:
        """
        Orchestrates notification sending with fallback logic:
        Push/WS -> Email -> SMS
        """
        self.background_tasks.add_task(self._process_fallback_notification, data)
        return True


    async def _process_fallback_notification(self, data: NotificationData):
        user = self.db.query(UserTable).filter(
            UserTable.user_id == data.user_id
        ).first()

        if not user:
            return

        notification_delivered = False

        # 1. Try WebSocket (Real-time)
        if data.push and check_online_user(user.user_id):
            await send_ws_notification(
                user.user_id, data.noty_type, data.title, data.body, data.image_url
            )
            notification_delivered = True

        # 2. Try Push Notification (FCM)
        if data.push:
            sessions = self.db.query(SessionTable).filter(
                SessionTable.user_id == user.user_id,
                SessionTable.is_login == True,
                SessionTable.fcm_token != None
            ).all()
            
            for session in sessions:
                if self.send_by_push(session.fcm_token, data):
                    notification_delivered = True

        if notification_delivered:
            return

        # 3. Fallback to Email
        if data.email and user.email_address:
            if self.send_by_email(user.email_address, data):
                return

        # 4. Fallback to SMS
        if data.sms and user.phone_number:
            self.send_by_sms(user.phone_number, data)




# ==============================================================================
# ==============================================================================
