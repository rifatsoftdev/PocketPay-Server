from fastapi import HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.constants import AnsiColor, String, ENV
from app.model import BankTable, WalletTable, TransactionTable
from app.enums import ActivityStatus, NotificationType, TransactionDirection, TransactionStatus, TransactionType, PaymentMethods
from app.schema import GlobalResponse, BankListOut, PocketToBankRequest, BankToPocketRequest
from app.utils import Helpers, Generators


class BankServises:
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
    
    def get_banks(self) -> GlobalResponse:
        try:
            bill_categories: List[BankTable] = self.db.query(BankTable).filter(
                BankTable.status == ActivityStatus.ACTIVE
            ).all()

            if not bill_categories:
                raise HTTPException(status_code=404, detail="Banks not found")

            # Serialize using Pydantic v2
            bank_out = [BankListOut.from_orm(p) for p in bill_categories]

            return GlobalResponse(
                success=True,
                message="Bank list fetched successfully",
                data={
                    "banks": bank_out
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def pocket_to_bank(self, payload: PocketToBankRequest) -> GlobalResponse:
        try:
            amount: Decimal = payload.amount
            reference: str = payload.reference if payload.reference else "N/A"

            user = verify_user(
                db=self.db,
                user_id=payload.user_id,
                access_token=payload.access_token,
                android_id=payload.android_id,
                android_uuid=payload.android_uuid,
                password=payload.password
            )

            bank = self.db.query(BankTable).filter(
                BankTable.bank_id == payload.bank_id,
                BankTable.status == ActivityStatus.ACTIVE
            ).first()
            if not bank:
                raise HTTPException(status_code=404, detail="Bank not found")

            wallet = self.db.query(WalletTable).filter(WalletTable.user_id == user.user_id).first()
            if not wallet:
                raise HTTPException(status_code=404, detail=String.WALLET_NOT_FOUND)

            charge: list = ServiceCharges.service_charge(amount, ENV.SERVICE_CHARGE)  # [amount, charge, total]
            if wallet.balance < charge[2]:
                raise HTTPException(status_code=400, detail=String.INSUFFICIENT_BALANCE)

            transaction_id = Generators.generate_transaction_id()
            transaction = TransactionTable(
                transaction_id=transaction_id,
                transaction_type=TransactionType.WITHDRAW,
                method=PaymentMethods.BANK,
                sender_user_id=user.user_id,
                sender_account=user.phone_number,
                receiver_account=payload.bank_account,
                receiver_user_id=None,
                account_id=bank.bank_id,
                account_name=bank.bank_name,
                currency="BDT",
                amount=Decimal(str(charge[0])),
                service_charge=charge[1],
                reference=reference,
                direction=TransactionDirection.OUT,
                status=TransactionStatus.SUCCESS,
                meta_data={
                    "bank_account_name": payload.bank_account_name,
                    "bank_logo": bank.bank_logo
                }
            )
            self.db.add(transaction)
            self.db.flush()

            wallet.balance -= Decimal(str(charge[2]))
            wallet.last_updated = Helpers.utc6dhaka()

            notifier = NotificationManager(self.db)
            notifier.send_user_notification(
                background_tasks=self.background_tasks,
                user_id=user.user_id,
                title="Bank Transfer",
                short_body=f"You have successfully transferred {charge[0]} TK to {bank.bank_name}. Service Charge: {charge[1]} TK. Total Deducted: {charge[2]} TK.",
                long_body=None,
                noty_type=NotificationType.TRANSACTION,
                image_url=None,
                push=True,
                sms=False,
                email=False
            )

            self.db.commit()
            self.db.refresh(wallet)
            self.db.refresh(transaction)

            return GlobalResponse(
                success=True,
                message="Pocket to bank transfer successful",
                data={
                    "transaction_id": transaction_id,
                    "amount": float(amount),
                    "status": TransactionStatus.SUCCESS.value
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def bank_to_pocket(self, payload: BankToPocketRequest):
        try:
            amount: Decimal = payload.amount
            reference: str = payload.reference if payload.reference else "N/A"

            user = verify_user(
                db=self.db,
                user_id=payload.user_id,
                access_token=payload.access_token,
                android_id=payload.android_id,
                android_uuid=payload.android_uuid,
                password=payload.password
            )

            bank = self.db.query(BankTable).filter(
                BankTable.bank_id == payload.bank_id,
                BankTable.status == ActivityStatus.ACTIVE
            ).first()
            if not bank:
                raise HTTPException(status_code=404, detail="Bank not found")

            wallet = self.db.query(WalletTable).filter(WalletTable.user_id == user.user_id).first()
            if not wallet:
                raise HTTPException(status_code=404, detail=String.WALLET_NOT_FOUND)

            transaction_id = Generators.generate_transaction_id()
            transaction = TransactionTable(
                transaction_id=transaction_id,
                transaction_type=TransactionType.DEPOSIT,
                method=PaymentMethods.BANK,
                sender_user_id=user.user_id,
                sender_account=payload.bank_account,
                receiver_account=user.phone_number,
                receiver_user_id=user.user_id,
                account_id=bank.bank_id,
                account_name=bank.bank_name,
                currency="BDT",
                amount=Decimal(str(amount)),
                service_charge=Decimal("0.00"),
                reference=reference,
                direction=TransactionDirection.IN,
                status=TransactionStatus.SUCCESS,
                meta_data={
                    "bank_account_name": payload.bank_account_name,
                    "bank_logo": bank.bank_logo
                }
            )
            self.db.add(transaction)
            self.db.flush()

            wallet.balance += Decimal(str(amount))
            wallet.last_updated = Helpers.utc6dhaka()

            notifier = NotificationManager(db)
            notifier.send_user_notification(
                background_tasks=self.background_tasks,
                user_id=user.user_id,
                title="Bank Deposit",
                short_body=f"You have successfully added {amount} TK from {bank.bank_name} to your wallet.",
                long_body=None,
                noty_type=NotificationType.TRANSACTION,
                image_url=None,
                push=True,
                sms=False,
                email=False
            )

            self.db.commit()
            self.db.refresh(wallet)
            self.db.refresh(transaction)

            return GlobalResponse(
                success=True,
                message="Bank to pocket transfer successful",
                data={
                    "transaction_id": transaction_id,
                    "amount": float(amount),
                    "status": TransactionStatus.SUCCESS.value
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

