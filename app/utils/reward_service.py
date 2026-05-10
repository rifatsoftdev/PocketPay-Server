from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import BackgroundTasks
from decimal import Decimal

from app.enums.transactions_enum import TransactionType, TransactionDirection, TransactionStatus
from app.enums.enums import *

from app.utils.generators import Generators
from app.utils.notification_manager import NotificationManager

from app.model import UserTable,WalletTable, TransactionTable



SYSTEM_ACCOUNT = "PocketPay"


class RewardService:
    """Service to handle user rewards."""

    @staticmethod
    def send_reward(
        background_tasks: BackgroundTasks,
        db: Session,
        user_id: str,
        title: str,
        body: str,
        amount: Decimal,
    ):
        try:
            if amount <= 0:
                raise ValueError("Reward amount must be greater than zero")

            wallet = db.query(WalletTable).filter_by(user_id=user_id).first()
            user = db.query(UserTable).filter_by(user_id=user_id).first()

            if not wallet or not user:
                raise ValueError("User or wallet not found")

            # ✅ Update wallet
            wallet.balance += amount

            # ✅ Create transaction
            transaction = TransactionTable(
                transaction_id=Generators.generate_transaction_id(),
                transaction_type=TransactionType.REWARD,
                method=PaymentMethods.WALLET,
                sender_user_id=SYSTEM_ACCOUNT,
                receiver_user_id=user_id,
                sender_account=SYSTEM_ACCOUNT,
                receiver_account=user.phone_number,
                currency="BDT",
                amount=amount,
                reference="N/A",
                direction=TransactionDirection.IN,
                status=TransactionStatus.SUCCESS,
            )
            db.add(transaction)

            db.flush()

            # real time notification
            notifier = NotificationManager(db)

            notifier.send_user_notification(
                background_tasks=background_tasks,
                user_id=user_id,
                title=title,
                short_body=body,
                long_body=None,
                noty_type="reward",
                image_url=None,
                push=True,
                sms=False,
                email=False
            )

            return transaction

        except SQLAlchemyError:
            db.rollback()
            raise

        except Exception:
            db.rollback()
            raise
