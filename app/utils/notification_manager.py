from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.router.notify_router import check_online_user, send_notification

# from app.model import UserTable, SessionTable

from app.model import UserTable, SessionTable

from app.dependencies.fcm_notification import FCMNotification
from app.dependencies.email_serivce import EmailSent




class NotificationManager:
    def __init__(self, db: Session):
        self.db = db
        self.fmcNotification = FCMNotification(
            "app/config/pocketpay-9a4ee-firebase-adminsdk-fbsvc-ad762430f4.json"
        )

    def send_user_notification(
        self,
        background_tasks: BackgroundTasks, 
        user_id: str,
        title: str, 
        short_body: str,
        long_body: str = None,
        noty_type: str = "general", 
        image_url: str = None,
        push: bool = True,
        sms: bool = False,
        email: bool = False
    ):
        user = self.db.query(UserTable).filter(UserTable.user_id == user_id).first()
        if not user:
            return

        # Push notification
        if push:
            if check_online_user(user_id):
                background_tasks.add_task(
                    send_notification, 
                    user_id, 
                    noty_type, 
                    title, 
                    short_body, 
                    image_url
                )
            else:
                fcm_record = self.db.query(SessionTable).filter(
                    SessionTable.user_id == user_id,
                    SessionTable.is_login == True
                ).first()

                if fcm_record and fcm_record.fcm_token:
                    background_tasks.add_task(
                        self.fmcNotification.send_single,
                        fcm_token=fcm_record.fcm_token,
                        type=noty_type,
                        title=title,
                        body=short_body,
                        img_url=image_url
                    )

        # Email
        if email and long_body and user.email_address:
            background_tasks.add_task(
                EmailSent.send_email,
                user.email_address,
                title,
                long_body
            )

        # SMS
        if sms and user.phone_number:
            background_tasks.add_task(
                "SMSSent.send_sms,",
                user.phone_number,
                title,
                short_body
            )





# ==============================================================================
# ==============================================================================
