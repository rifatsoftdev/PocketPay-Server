from fastapi import HTTPException, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import or_
from decimal import Decimal

from app.constants import String, AnsiColor
from app.enums import TransactionType, PaymentMethods, TransactionDirection, TransactionStatus, NotificationType
from app.schema import PaymentRequest, GlobalResponse, GlobalRequest
from app.model import DevTable, UserTable, WalletTable, TransactionTable
from app.utils import Generators, Helpers

from app.services.auth.user_verification import UserVerificationService
from app.services.notification.noticication_services import NotificationServices, NotificationData


class HistoryServices:
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
    
    def all_transactions(self, user_id: str) -> GlobalResponse:
        try:
            # Fetch sorted transactions (LIMIT 100 each)
            sent_list = (
                self.db.query(TransactionTable)
                .filter(TransactionTable.sender_user_id == user_id)
                .order_by(TransactionTable.created_at.desc())
                .limit(100)
                .all()
            )

            received_list = (
                self.db.query(TransactionTable)
                .filter(TransactionTable.receiver_user_id == user_id)
                .order_by(TransactionTable.created_at.desc())
                .limit(100)
                .all()
            )

            # Two Pointer Merge
            i = j = 0
            merged = []

            while len(merged) < 100 and i < len(sent_list) and j < len(received_list):
                if sent_list[i].created_at > received_list[j].created_at:
                    merged.append(sent_list[i])
                    i += 1
                else:
                    merged.append(received_list[j])
                    j += 1

            while len(merged) < 100 and i < len(sent_list):
                merged.append(sent_list[i])
                i += 1

            while len(merged) < 100 and j < len(received_list):
                merged.append(received_list[j])
                j += 1

            # ===== Serialize for JSON =====
            transactions = []
            for tx in merged:
                transactions.append({
                    "transaction_id": tx.transaction_id,
                    "transaction_type": tx.transaction_type.value,
                    "method": tx.method.value,
                    "sender_user_id": tx.sender_user_id,
                    "receiver_user_id": tx.receiver_user_id,
                    "sender_account": tx.sender_account,
                    "receiver_account": tx.receiver_account,
                    "currency": tx.currency,
                    "amount": float(tx.amount),
                    "service_charge": float(tx.service_charge),
                    "reference": tx.reference,
                    "direction": tx.direction.value,
                    "status": tx.status.value,
                    "created_at": tx.created_at.isoformat()
                })
            # print(transactions)

            return GlobalResponse(
                success=True,
                status="success",
                message="Last 100 transactions fetched successfully",
                data={
                    "transactions": transactions
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}ERROR{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def all_notifications(self, user_id: str) -> GlobalResponse:
        try:
            notifications_list = []

            user: UserTable = self.db.query(UserTable).filter(
                UserTable.user_id == user_id
            ).first()

            for tx in user.notifications:
                notifications_list.append({
                    "id": tx.id,
                    "type": tx.type,
                    "title": tx.title,
                    "body": tx.body,
                    "img_url": tx.img_url,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                    "is_read": tx.is_read
                })

            return GlobalResponse(
                success=True,
                message="All transactions fetched successfully",
                data={
                    "notifications": notifications_list[::-1]
                }
            )
        
        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def transaction_details(self, transaction_id: str) -> GlobalResponse:
        try:
            access_token = Helpers.authorization(self.authorization)

            user_verification_service = UserVerificationService(
                db=self.db,
                background_tasks=self.background_tasks,
                request=self.request,
                authorization=self.authorization
            )

            user_id: str = user_verification_service.verify_access_token(access_token=access_token)

            tx = self.db.query(TransactionTable).filter(
                TransactionTable.transaction_id == transaction_id
            ).first()

            if not tx:
                raise HTTPException(
                    status_code=404,
                    detail="Transaction not found"
                )

            return GlobalResponse(
                success=True,
                message="Transaction fetched successfully",
                data={
                    "transaction_id": tx.transaction_id,
                    "transaction_type": tx.transaction_type.value,
                    "method": tx.method.value,
                    "sender_user_id": tx.sender_user_id,
                    "receiver_user_id": tx.receiver_user_id,
                    "sender_account": tx.sender_account,
                    "receiver_account": tx.receiver_account,
                    "currency": tx.currency,
                    "amount": float(tx.amount) if tx.amount is not None else None,
                    "service_charge": float(tx.service_charge) if tx.service_charge is not None else None,
                    "reference": tx.reference,
                    "direction": tx.direction.value,
                    "status": tx.status.value,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)


