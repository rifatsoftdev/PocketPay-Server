from datetime import timedelta
from fastapi import BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from datetime import datetime, timezone, timedelta


from app.constants import AnsiColor, String
from app.enums import NotificationType, TransactionStatus
from app.model import (
    DeletedUserTable, NotificationTable, SessionTable, SettingsTable,
    AdminTable, UserTable, TransactionTable, WalletTable
)
from app.schema import GlobalResponse, CancelDeleteAccountRequest
from app.utils import Helpers, Generators, Hashing

from app.model.admin_table import AdminRole
from app.services.auth.user_verification import UserVerificationService
from app.schema.auth_schemas import DeleteAccountRequest
from app.services.auth.user_verification import UserVerificationService


today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


class AdminAccessServices(UserVerificationService):
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
    
    def get_dashboard_stats(self) -> GlobalResponse:
        try:
            # Basic counts
            total_users = self.db.query(UserTable).count()

            active_users = self.db.query(SettingsTable).filter(
                SettingsTable.account_locked == False
            ).count()
            
            deactive_user = total_users - active_users
            # Today's stats
            new_users_today = self.db.query(UserTable).filter(
                UserTable.created_at >= today_start
            ).count()
            
            # Transaction stats
            total_transactions = self.db.query(TransactionTable).count()
            total_tx_amount = self.db.query(func.sum(TransactionTable.amount)).scalar() or 0
            total_profite = self.db.query(func.sum(TransactionTable.service_charge)).scalar() or 0
            transactions_today = self.db.query(TransactionTable).filter(
                TransactionTable.created_at >= today_start
            ).count()

            status_counts = {
                "pending": self.db.query(TransactionTable).filter(TransactionTable.status == TransactionStatus.PENDING.value).count(),
                "success": self.db.query(TransactionTable).filter(TransactionTable.status == TransactionStatus.SUCCESS.value).count(),
                "failed": self.db.query(TransactionTable).filter(TransactionTable.status == TransactionStatus.FAILED.value).count(),
                "cancelled": self.db.query(TransactionTable).filter(TransactionTable.status == TransactionStatus.CANCELLED.value).count(),
                "refunded": self.db.query(TransactionTable).filter(TransactionTable.status == TransactionStatus.REFUNDED.value).count(),
            }


            # Wallet balance
            total_wallets_balance = self.db.query(func.sum(WalletTable.balance)).scalar() or 0
            
            amount_today = self.db.query(func.sum(TransactionTable.amount)).filter(
                TransactionTable.created_at >= today_start
            ).scalar() or 0

            # Recent activity
            recent_transactions = self.db.query(TransactionTable).order_by(desc(TransactionTable.created_at)).limit(5).all()
            recent_users = self.db.query(UserTable).order_by(desc(UserTable.created_at)).limit(5).all()
            
            # print(f"{total_users} {active_users} {total_transactions} {total_tx_amount} {total_wallets_balance} {new_users_today} {transactions_today} {amount_today}")
            
            return GlobalResponse(
                success=True,
                message="Dashboard statistics retrieved successfully",
                data={
                    "total_users": total_users,
                    "active_users": active_users,
                    "deactive_user": deactive_user,
                    "new_users_today": new_users_today,
                    "total_profite": float(total_profite),
                    "total_transactions": total_transactions,
                    "total_transaction_amount": float(total_tx_amount),
                    "total_wallets_balance": float(total_wallets_balance),
                    "transactions_today": transactions_today,
                    "amount_today": float(amount_today),
                    "status_counts": status_counts,
                    "recent_transactions": [
                        {
                            "transaction_id": tx.transaction_id,
                            "transaction_type": str(tx.transaction_type),
                            "amount": float(tx.amount),
                            "currency": tx.currency,
                            "status": str(tx.status),
                            "created_at": tx.created_at
                        } for tx in recent_transactions
                    ],
                    "recent_users": [
                        {
                            "user_id": user.user_id,
                            "full_name": user.full_name,
                            "email": user.email_address,
                            "phone": user.phone_number,
                            "created_at": user.created_at
                        } for user in recent_users
                    ]
                }
            )
            
        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
