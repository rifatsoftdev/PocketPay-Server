from datetime import timedelta
from fastapi import BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session

from app.constants import AnsiColor, String
from app.enums import NotificationType
from app.model import DeletedUserTable, NotificationTable, SessionTable, SettingsTable, AdminTable
from app.schema import GlobalResponse, CancelDeleteAccountRequest
from app.utils import Helpers, Generators, Hashing

from app.model.admin_table import AdminRole
from app.services.auth.user_verification import UserVerificationService
from app.schema.auth_schemas import DeleteAccountRequest
from app.services.auth.user_verification import UserVerificationService




class AdminManagementServices(UserVerificationService):
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
    
    