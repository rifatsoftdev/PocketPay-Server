from pydantic import BaseModel

from app.enums import NotificationType, NotificationCreator


class AdminNotyfyResuest(BaseModel):
    user_id: str

    type: str = NotificationType.ALERT
    title: str
    body: str
    image_url: str | None = None

    button_text: str | None = None
    button_link: str | None = None
    send_push: bool = True
    send_email: bool = False
    send_sms: bool = False
