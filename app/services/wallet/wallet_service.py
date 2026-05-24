import os, json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from decimal import Decimal, ROUND_HALF_UP

from app.constants import AnsiColor, String, ENV
from app.utils import Generators, Helpers
from app.enums import ActivityStatus, PaymentMethods, TransactionDirection, TransactionStatus, TransactionType
from app.model import MobileOperatorTable, TransactionTable, UserTable, WalletTable
from app.schema import GlobalResponse, MobileRechargeRequest, SendMoneyRequest

from app.services.auth.user_verification import UserVerificationService

from app.services.notification.noticication_services import NotificationServices, NotificationData


class BalanceData:
    def __init__(self, balance: str, currency: str, last_updated: str):
        self.balance: str = balance
        self.currency: str = currency
        self.last_updated: str = last_updated


class ServiceChargeData:
    def __init__(self, amount: Decimal, charge: Decimal, total: Decimal):
        self.amount = amount
        self.charge = charge
        self.total = total


class WalletService:
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

    def __get_balance(self, user_id: str) -> BalanceData:
        try:
            wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == user_id
            ).first()
            
            return BalanceData(
                wallet.balance,
                wallet.currency,
                wallet.last_updated
            )
        
        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(
                status_code=500,
                detail=String.SERVER_ERROR
            )
    
    def get_balance(self) -> GlobalResponse:
        access_token = Helpers.authorization(self.authorization)

        # verify user
        userVerificationService = UserVerificationService(
            db=self.db,
            background_tasks=self.background_tasks,
            request=self.request,
            authorization=self.authorization
        )

        user_id: str = userVerificationService.verify_access_token(access_token=access_token)   
        wallet: BalanceData = self.__get_balance(user_id)

        return GlobalResponse(
            success=True,
            message="Balance retrieved successfully",
            data={
                "balance": wallet.balance,
                "currency": wallet.currency,
                "last_updated": wallet.last_updated.isoformat() if wallet.last_updated else None
            }
        )
    
    def __take_profit(self, amount: float) -> None:
        JSON_DB = "data/pocketpay.json"

        # JSON read
        with open(JSON_DB, "r") as file:
            data = json.load(file)

        from decimal import Decimal

        data["admin_profit"] = str(
            Decimal(str(data.get("admin_profit", 0))) + Decimal(str(amount))
        )

        # JSON write
        with open(JSON_DB, "w") as file:
            json.dump(data, file, indent=4)
    
    def service_charge(self, amount: Decimal) -> ServiceChargeData:
        charge_percent = Decimal(str(ENV.SERVICE_CHARGE))
        amount = Decimal(str(amount))

        if amount < 0:
            raise ValueError("Amount cannot be negative.")
        if charge_percent < 0:
            raise ValueError("Service charge percentage cannot be negative.")

        charge = (amount * charge_percent / Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        return ServiceChargeData(amount, charge, amount + charge)

    @staticmethod
    def _phone_lookup_values(phone: str) -> set[str]:
        phone = (phone or "").strip()
        compact_phone = "".join(
            char for char in phone if char.isdigit() or char == "+"
        )

        values = {phone, compact_phone}
        if compact_phone.startswith("+"):
            values.add(compact_phone[1:])

        digits_only = "".join(char for char in compact_phone if char.isdigit())
        if digits_only:
            values.add(digits_only)

        for country_code in ("880", "91"):
            if digits_only.startswith(country_code) and len(digits_only) > len(country_code):
                local_number = digits_only[len(country_code):]
                values.add(local_number)
                values.add(f"0{local_number}")

        return {value for value in values if value}
    
    def process_transaction(
        self,
        sender_id: str,
        receiver_id: str,
        amount: Decimal,
        trx_type: TransactionType
    ) -> bool:
        try:
            if amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Amount must be greater than zero"
                )

            if sender_id == receiver_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sender and receiver cannot be same"
                )

            sender_wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == sender_id
            ).with_for_update().first()

            receiver_wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == receiver_id
            ).with_for_update().first()

            if not sender_wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sender's wallet not found"
                )

            if not receiver_wallet:
                raise HTTPException(
                    status_code=404,
                    detail="Receiver's wallet not found"
                )

            sender = self.db.query(UserTable).filter(
                UserTable.user_id == sender_id
            ).first()
            receiver = self.db.query(UserTable).filter(
                UserTable.user_id == receiver_id
            ).first()

            if not sender:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sender not found"
                )

            if not receiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Receiver not found"
                )

            charge: ServiceChargeData = self.service_charge(amount)

            if sender_wallet.balance < charge.total:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=String.INSUFFICIENT_BALANCE
                )

            sender_account = (sender.country_code + sender.phone_number) if sender.phone_number else (sender.email_address or sender.user_id)
            receiver_account = (
                f"{receiver.country_code or ''}{receiver.phone_number}"
                if receiver.phone_number
                else (receiver.email_address or receiver.user_id)
            )

            transaction = TransactionTable(
                transaction_id=Generators.generate_transaction_id(),
                transaction_type=trx_type,
                method=PaymentMethods.WALLET,
                sender_user_id=sender_id,
                sender_account=sender_account,
                receiver_user_id=receiver_id,
                receiver_account=receiver_account,
                account_id=None,
                account_name=None,
                currency=sender_wallet.currency or "BDT",
                amount=charge.amount,
                service_charge=charge.charge,
                reference="N/A",
                direction=TransactionDirection.OUT,
                status=TransactionStatus.SUCCESS
            )

            self.db.add(transaction)
            self.db.flush()

            sender_wallet.balance -= charge.total
            sender_wallet.total_debits = (sender_wallet.total_debits or Decimal("0")) + charge.total
            sender_wallet.last_updated = Helpers.utc6dhaka()

            receiver_wallet.balance += charge.amount
            receiver_wallet.total_credits = (receiver_wallet.total_credits or Decimal("0")) + charge.amount
            receiver_wallet.last_updated = Helpers.utc6dhaka()

            self.__take_profit(charge.charge)

            self.db.commit()

            return True

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(
                status_code=500,
                detail=String.SERVER_ERROR
            )
    
    def cancel_transaction(self, tnx_id: str) -> GlobalResponse:
        try:
            # 1. Finding transaction data (Locking for safety)
            transaction = self.db.query(TransactionTable).filter(
                TransactionTable.transaction_id == tnx_id
            ).with_for_update().first()

            if not transaction:
                raise HTTPException(status_code=404, detail="Transaction not found")

            # 2. Check the time (not more than 1 minute)
            now = datetime.now(timezone.utc)
            created_at = transaction.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            time_diff = (now - created_at).total_seconds()
            
            if time_diff > 60:
                raise HTTPException(
                    status_code=400, 
                    detail="Cancellation time expired. You can only cancel within 1 minute."
                )

            # 3. Checking the status (only SUCCESS transactions can be canceled)
            if transaction.status == TransactionStatus.CANCELLED:
                raise HTTPException(status_code=400, detail="Transaction is already cancelled")
            
            if transaction.status != TransactionStatus.SUCCESS:
                raise HTTPException(status_code=400, detail="Only successful transactions can be cancelled")

            # 4. Reverting the sender's balance (returning money + service charge)
            sender_wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == transaction.sender_user_id
            ).with_for_update().first()

            if sender_wallet:
                revert_total = transaction.amount + (transaction.service_charge or Decimal("0"))
                sender_wallet.balance += revert_total
                sender_wallet.total_debits = (sender_wallet.total_debits or Decimal("0")) - revert_total
                sender_wallet.last_updated = Helpers.utc6dhaka()

            # 5. Reverting the receiver's balance (if it was P2P or sent money)
            if transaction.receiver_user_id:
                receiver_wallet = self.db.query(WalletTable).filter(
                    WalletTable.user_id == transaction.receiver_user_id
                ).with_for_update().first()
                
                if receiver_wallet:
                    receiver_wallet.balance -= transaction.amount
                    receiver_wallet.total_credits = (receiver_wallet.total_credits or Decimal("0")) - transaction.amount
                    receiver_wallet.last_updated = Helpers.utc6dhaka()

            # 6. Reverting admin profits
            if transaction.service_charge and transaction.service_charge > 0:
                self.__revert_profit(float(transaction.service_charge))

            # 7. Updating transaction status
            transaction.status = TransactionStatus.CANCELLED
            transaction.updated_at = Helpers.utc6dhaka()

            self.db.commit()

            return GlobalResponse(
                success=True,
                message="Transaction cancelled and money refunded successfully",
                data={"transaction_id": tnx_id}
            )

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     Cancel Trx Error: {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
    
    def send_reward(
        self,
        user_id: str,
        title: str,
        body: str,
        amount: Decimal,
    ):
        try:
            # print(String.SYSTEM_USER_ID, user_id)
            process_status: bool = self.process_transaction(
                sender_id=String.SYSTEM_USER_ID,
                receiver_id=user_id,
                amount=amount,trx_type=TransactionType.REWARD
            )

            if process_status:
                try:
                    notificationServices = NotificationServices(
                        db=self.db,
                        background_tasks=self.background_tasks
                    )

                    notificationServices.send_notification(NotificationData(
                        user_id=user_id,
                        template="transaction.reward",
                        context={
                            "amount": amount,
                            "reference": body or title,
                        },
                        noty_type="reward",
                    ))
                    
                except Exception as e:
                    print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     Reward notification failed: {e}")
                    

        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def __revert_profit(self, amount: float) -> None:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_db = os.path.join(current_dir, '..', 'data', 'pocketpay.json')
            json_db = os.path.abspath(json_db)
            with open(json_db, "r") as file: data = json.load(file)
            data["admin_profit"] = data.get("admin_profit", 0) - amount
            with open(json_db, "w") as file: json.dump(data, file, indent=4)
        except: pass
    
    def send_money(
        self,
        payload: SendMoneyRequest
    ) -> GlobalResponse:
        try:
            recipient_phone: str = payload.recipient_phone
            recipient_lookup_values = self._phone_lookup_values(recipient_phone)
            amount = Decimal(str(payload.amount))
            reference: str = payload.reference if payload.reference else "N/A"

            access_token = Helpers.authorization(self.authorization)

            user_verification_service = UserVerificationService(
                db=self.db,
                background_tasks=self.background_tasks,
                request=self.request,
                authorization=self.authorization
            )

            sender = user_verification_service.verify_user(
                user_id=payload.user_id,
                access_token=access_token,
                device_id=payload.device_id,
                device_uuid=payload.device_uuid,
                password=payload.user_password,
                advance_check=True
            )

            if amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be greater than zero")

            combined_phone = (
                func.coalesce(UserTable.country_code, "")
                + func.coalesce(UserTable.phone_number, "")
            )
            combined_phone_without_plus = func.replace(combined_phone, "+", "")

            receiver_filters = [
                UserTable.phone_number.in_(recipient_lookup_values),
                combined_phone.in_(recipient_lookup_values),
                combined_phone_without_plus.in_(recipient_lookup_values),
                UserTable.email_address == recipient_phone,
                UserTable.user_id == recipient_phone
            ]

            receiver = self.db.query(UserTable).filter(
                or_(*receiver_filters)
            ).first()

            if not receiver:
                raise HTTPException(
                    status_code=404,
                    detail="Receiver not found"
                )

            if sender.user_id == receiver.user_id:
                raise HTTPException(status_code=400, detail="Sender and receiver cannot be same")

            sender_wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == sender.user_id
            ).with_for_update().first()

            receiver_wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == receiver.user_id
            ).with_for_update().first()

            if not sender_wallet:
                raise HTTPException(status_code=404, detail="Sender's wallet not found")
            
            if not receiver_wallet:
                raise HTTPException(status_code=404, detail="Receiver's wallet not found")

            charge: ServiceChargeData = self.service_charge(amount)

            if sender_wallet.balance < charge.total:
                raise HTTPException(status_code=400, detail=String.INSUFFICIENT_BALANCE)

            transaction_id = Generators.generate_transaction_id()
            sender_account = (sender.country_code + sender.phone_number) if sender.phone_number else (sender.email_address or sender.user_id)
            receiver_account = (receiver.country_code + receiver.phone_number) if receiver.phone_number else (receiver.email_address or receiver.user_id)

            transaction = TransactionTable(
                transaction_id=transaction_id,
                transaction_type=TransactionType.SENDMONEY,
                method=PaymentMethods.WALLET,
                sender_user_id=sender.user_id,
                sender_account=sender_account,
                receiver_account=receiver_account,
                receiver_user_id=receiver.user_id,
                account_id=None,
                account_name=None,
                currency=sender_wallet.currency or "BDT",
                amount=charge.amount,
                service_charge=charge.charge,
                reference=reference,
                direction=TransactionDirection.OUT,
                status=TransactionStatus.SUCCESS
            )
            self.db.add(transaction)
            self.db.flush()
            
            sender_wallet.balance -= charge.total
            sender_wallet.total_debits = (sender_wallet.total_debits or Decimal("0")) + charge.total
            sender_wallet.last_updated = Helpers.utc6dhaka()

            receiver_wallet.balance += charge.amount
            receiver_wallet.total_credits = (receiver_wallet.total_credits or Decimal("0")) + charge.amount
            receiver_wallet.last_updated = Helpers.utc6dhaka()

            try:
                notificationServices = NotificationServices(
                    db=self.db,
                    background_tasks=self.background_tasks
                )

                notificationServices.send_notification(NotificationData(
                    user_id=receiver.user_id,
                    template="transaction.receive_money",
                    context={
                        "amount": charge.amount,
                        "sender": sender_account,
                        "reference": reference,
                        "transaction_id": transaction_id,
                    },
                    noty_type="transaction",
                ))

                notificationServices.send_notification(NotificationData(
                    user_id=sender.user_id,
                    template="transaction.send_money",
                    context={
                        "amount": charge.amount,
                        "receiver": receiver_account,
                        "service_charge": charge.charge,
                        "total": charge.total,
                        "reference": reference,
                        "transaction_id": transaction_id,
                    },
                    noty_type="transaction",
                ))

                
            except Exception as e:
                print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     Send money notification failed: {e}")

            self.db.commit()
            self.db.refresh(sender_wallet)
            self.db.refresh(receiver_wallet)
            self.db.refresh(transaction)

            return GlobalResponse(
                success=True,
                message="Sent money successfully",
                data={
                    "transaction_id": transaction_id,
                    "amount": float(charge.amount),
                    "service_charge": float(charge.charge),
                    "total_deducted": float(charge.total),
                    "status": "completed"
                }
            )
        
        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    
