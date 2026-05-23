from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

from app.model import SessionTable


class SessionService:

    # --------------------------------------------------
    # 1️⃣ Check login (API guard)
    # --------------------------------------------------
    @staticmethod
    def check_login(
        db: Session,
        user_id: str,
        android_id: str,
        uuid: str
    ) -> bool:
        try:
            session = db.query(SessionTable).filter(
                SessionTable.user_id == user_id,
                SessionTable.device_id == android_id,
                SessionTable.device_uuid == uuid,
                SessionTable.is_login == True
            ).first()

            return session is not None

        except SQLAlchemyError as e:
            print("DB ERROR check_login:", e)
            return False


    # --------------------------------------------------
    # 3️⃣ Logout (normal logout)
    # --------------------------------------------------
    @staticmethod
    def perform_logout(
        db: Session,
        user_id: str,
        android_id: str,
        uuid: str
    ) -> bool:
        try:
            session = db.query(SessionTable).filter(
                SessionTable.user_id == user_id,
                SessionTable.device_id == android_id,
                SessionTable.device_uuid == uuid,
                SessionTable.is_login == True
            ).first()

            if not session:
                return False

            session.is_login = False
            session.logout_at = datetime.utcnow()

            db.commit()
            return True

        except SQLAlchemyError as e:
            db.rollback()
            print("DB ERROR perform_logout:", e)
            return False


    # --------------------------------------------------
    # 4️⃣ Get active session (READ ONLY)
    # --------------------------------------------------
    @staticmethod
    def get_active_session(
        db: Session,
        user_id: str,
        android_id: str,
        uuid: str
    ) -> SessionTable | None:
        try:
            return db.query(SessionTable).filter(
                SessionTable.user_id == user_id,
                SessionTable.device_id == android_id,
                SessionTable.device_uuid == uuid,
                SessionTable.is_login == True
            ).first()

        except SQLAlchemyError as e:
            print("DB ERROR get_active_session:", e)
            return None


    # --------------------------------------------------
    # 6️⃣ Heartbeat / last seen update
    # --------------------------------------------------
    @staticmethod
    def update_last_seen(
        db: Session,
        user_id: str,
        android_id: str,
        uuid: str
    ) -> bool:
        try:
            session = db.query(SessionTable).filter(
                SessionTable.user_id == user_id,
                SessionTable.device_id == android_id,
                SessionTable.device_uuid == uuid,
                SessionTable.is_login == True
            ).first()

            if not session:
                return False

            session.last_seen_at = datetime.utcnow()
            db.commit()
            return True

        except SQLAlchemyError as e:
            db.rollback()
            print("DB ERROR update_last_seen:", e)
            return False


    # --------------------------------------------------
    # 8️⃣ Force logout user (admin / security)
    # --------------------------------------------------
    @staticmethod
    def force_logout_user(
        db: Session,
        user_id: str
    ) -> int:
        try:
            result = db.query(SessionTable).filter(
                SessionTable.user_id == user_id,
                SessionTable.is_login == True
            ).update({
                "is_login": False,
                "logout_at": datetime.utcnow()
            })

            db.commit()
            return result

        except SQLAlchemyError as e:
            db.rollback()
            print("DB ERROR force_logout_user:", e)
            return 0


    # --------------------------------------------------
    # 9️⃣ Cleanup old sessions (cron job)
    # --------------------------------------------------
    @staticmethod
    def cleanup_old_sessions(
        db: Session,
        days: int = 90
    ) -> int:
        try:
            threshold = datetime.utcnow() - timedelta(days=days)

            result = db.query(SessionTable).filter(
                SessionTable.login_at == False,
                SessionTable.logout_at < threshold
            ).delete()

            db.commit()
            return result

        except SQLAlchemyError as e:
            db.rollback()
            print("DB ERROR cleanup_old_sessions:", e)
            return 0
