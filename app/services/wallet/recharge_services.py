from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.constants import String, AnsiColor
from app.model import WalletTable, TransactionTable, MobileOperatorTable, AdminTable, AdminSessionTable
from app.enums import NotificationType, ActivityStatus, TransactionType, TransactionStatus, TransactionDirection, PaymentMethods
from app.schema import MobileRechargeRequest, NewOperatorRequest, OperatorDeactivateRequest, OperatorActivateRequest, GlobalResponse
from app.utils import Generators, Hashing, Helpers, Token

from app.services.wallet.wallet_service import WalletService, ServiceChargeData
from app.services.auth.user_verification import UserVerificationService
from app.services.notification.noticication_services import NotificationServices, NotificationData



class RechargeServices(WalletService):
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

    def _is_admin_request(self) -> bool:
        try:
            if not self.authorization or not self.authorization.startswith("Bearer "):
                return False

            access_token = self.authorization.replace("Bearer ", "", 1)
            token_payload = Token().decode_token(access_token)

            if not token_payload or token_payload.get("type") != "access":
                return False

            admin_id = token_payload.get("admin_id")
            if not admin_id:
                return False

            admin = self.db.query(AdminTable).filter(
                AdminTable.admin_id == admin_id,
                AdminTable.is_active == True
            ).first()

            if not admin:
                return False

            sessions = self.db.query(AdminSessionTable).filter(
                AdminSessionTable.admin_id == admin_id,
                AdminSessionTable.is_login == True,
                AdminSessionTable.access_token_hash.isnot(None)
            ).all()

            return any(
                Hashing.verify_hash(access_token, session.access_token_hash)
                for session in sessions
            )

        except Exception:
            return False

    def _operator_to_dict(self, operator: MobileOperatorTable, include_admin_fields: bool = False) -> dict:
        data = {
            "operator_id": operator.operator_id,
            "operator_name": operator.operator_name,
            "country_code": operator.country_code,
            "logo_url": operator.logo_url
        }

        if include_admin_fields:
            data.update({
                "status": operator.status.value if operator.status else None,
                "operator_api": operator.operator_api,
                "meta_data": operator.meta_data,
                "created_at": operator.created_at.isoformat() if operator.created_at else None,
                "updated_at": operator.updated_at.isoformat() if operator.updated_at else None
            })

        return data
    
    def get_operators(self, country_code: str) -> GlobalResponse:
        try:
            if country_code:
                country_code = "+" + country_code[1::]

            is_admin_request = self._is_admin_request()
            query = self.db.query(MobileOperatorTable)

            if not is_admin_request:
                query = query.filter(MobileOperatorTable.status == ActivityStatus.ACTIVE)

            # Optional filter
            if country_code:
                query = query.filter(
                    MobileOperatorTable.country_code == country_code
                )

            operators = query.order_by(MobileOperatorTable.created_at.desc()).all()

            # if not operators:
            #     raise HTTPException(
            #         status_code=status.HTTP_404_NOT_FOUND, 
            #         detail="Mobile operators not found"
            #     )

            operators_list = [
                self._operator_to_dict(
                    operator=operator,
                    include_admin_fields=is_admin_request
                )
                for operator in operators
            ]

            return GlobalResponse(
                success=True,
                message="Mobile operators fetched successfully",
                data={
                    "operators": operators_list
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
    
    def mobile_recharge(
        self,
        payload: MobileRechargeRequest
    ) -> GlobalResponse:
        try:
            operator_id = payload.operator_id
            number = payload.number
            amount = Decimal(str(payload.amount))
            reference = payload.refarence if payload.refarence else "N/A"

            print(self.authorization)

            if amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be greater than zero")

            user_verification_service = UserVerificationService(self.db)
            user = user_verification_service.verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                android_id=payload.device_id,
                android_uuid=payload.device_uuid,
                password=payload.user_password,
                advance_check=True
            )

            operator = self.db.query(MobileOperatorTable).filter(
                MobileOperatorTable.operator_id == operator_id,
                MobileOperatorTable.status == ActivityStatus.ACTIVE
            ).first()

            if not operator:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mobile operator not found"
                )

            wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == user.user_id
            ).with_for_update().first()

            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=String.WALLET_NOT_FOUND
                )

            charge: ServiceChargeData = self.service_charge(amount)

            if wallet.balance < charge.total:
                raise HTTPException(status_code=400, detail=String.INSUFFICIENT_BALANCE)

            transaction_id = Generators.generate_transaction_id()
            sender_account = (user.country_code + user.phone_number) if user.phone_number else (user.email_address or user.user_id)

            transaction = TransactionTable(
                transaction_id=transaction_id,
                transaction_type=TransactionType.RECHARGE,
                method=PaymentMethods.WALLET,
                sender_user_id=user.user_id,
                sender_account=sender_account,
                receiver_account=number,
                receiver_user_id=None,
                account_id=operator.operator_id,
                account_name=operator.operator_name,
                currency=wallet.currency or "BDT",
                amount=charge.amount,
                service_charge=charge.charge,
                reference=reference,
                direction=TransactionDirection.OUT,
                status=TransactionStatus.SUCCESS
            )
            self.db.add(transaction)
            self.db.flush()

            wallet.balance -= charge.total
            wallet.total_debits = (wallet.total_debits or Decimal("0")) + charge.total
            wallet.last_updated = Helpers.utc6dhaka()
            
            try:
                notificationServices = NotificationServices(
                    db=self.db,
                    background_tasks=self.background_tasks
                )

                notificationServices.send_notification(NotificationData(
                    user_id=user.user_id,
                    title="Mobile Recharge",
                    body=f"You have successfully recharged {number} with {charge.amount} TK. Service Charge: {charge.charge} TK. Total Deducted: {charge.total} TK.",
                    noty_type="transaction",
                ))
                
            except Exception as e:
                print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     Send money notification failed: {e}")

            self.db.commit()
            self.db.refresh(transaction)
            self.db.refresh(wallet)

            return GlobalResponse(
                success=True,
                message="Mobile recharge successfully",
                data={
                    "transaction_id": transaction_id,
                    "amount": float(charge.amount),
                    "service_charge": float(charge.charge),
                    "total_deducted": float(charge.total),
                    "status": TransactionStatus.SUCCESS.value
                }
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def add_new_operator(self, payload: NewOperatorRequest) -> GlobalResponse:
        try:
            # Helpers.print_payload(payload)
            user_verification_service = UserVerificationService(
                db=self.db,
                background_tasks=self.background_tasks,
                request=self.request,
                authorization=self.authorization
            )

            user: AdminTable = user_verification_service.verify_admin(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=payload.android_id,
                device_uuid=payload.android_uuid,
                password=payload.user_password
            )
            
            # 🔍 Duplicate operator check (same name + country)
            existing_operator = self.db.query(MobileOperatorTable).filter(
                MobileOperatorTable.operator_name == payload.operator_name,
                MobileOperatorTable.country_code == payload.country_code
            ).first()

            if existing_operator:
                raise HTTPException(
                    status_code=409,
                    detail="Operator already exists for this country"
                )

            operator_id = Generators.generate_id("operator")

            # 🧱 Create operator object
            new_operator = MobileOperatorTable(
                operator_id=operator_id,
                operator_name=payload.operator_name,
                country_code=payload.country_code,
                logo_url=payload.logo_url,
                operator_api=payload.operator_api,
                status=ActivityStatus.PENDING,   # default
                meta_data={
                    "request_user": {
                        "user_id": user.admin_id,
                        "email_address": user.email,
                        "full_name": user.full_name
                    }
                }
            )
            self.db.add(new_operator)
            self.db.flush()

            
            # real time notification
            # notifier = NotificationManager(self.db)

            # notifier.send_user_notification(
            #     background_tasks=self.background_tasks,
            #     user_id=user.user_id,
            #     title="New Operator Added Request Received",
            #     short_body=f"You have requested to become a New Operator. The request was successful. Wait for your Operator ID {new_operator.operator_id} account to be activated.",
            #     long_body=None,
            #     noty_type=NotificationType.REQUEST,
            #     image_url=None,
            #     push=True,
            #     sms=False,
            #     email=False
            # )

            # db commit and refresh
            self.db.commit()
            self.db.refresh(new_operator)

            return GlobalResponse(
                success=True,
                message="New operator added successfully",
                data={
                    "operator_id": new_operator.operator_id,
                    "operator_name": new_operator.operator_name,
                    "country_code": new_operator.country_code,
                    "logo_url": new_operator.logo_url,
                    "operator_api": new_operator.operator_api,
                    "status": new_operator.status.value
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def deactivate_operator(self, payload: OperatorDeactivateRequest):
        try:
            user_verification_service = UserVerificationService(self.db)

            user = user_verification_service.verify_admin(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=payload.device_id,
                device_uuid=payload.device_uuid,
                password=payload.user_password
            )

            operator = self.db.query(MobileOperatorTable).filter(
                MobileOperatorTable.operator_id == payload.operator_id
            ).first()

            if not operator:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mobile operator not found"
                )

            operator.status = ActivityStatus.INACTIVE
            operator.updated_at = Helpers.utc6dhaka()
            self.db.commit()
            self.db.refresh(operator)

            return GlobalResponse(
                success=True,
                message="Operator deactivated successfully",
                data={
                    "operator_id": operator.operator_id,
                    "status": operator.status.value
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def activate_operator(self, payload: OperatorActivateRequest):
        try:
            user_verification_service = UserVerificationService(self.db)

            user = user_verification_service.verify_admin(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=payload.device_id,
                device_uuid=payload.device_uuid,
                password=payload.user_password
            )

            operator = self.db.query(MobileOperatorTable).filter(
                MobileOperatorTable.operator_id == payload.operator_id
            ).first()

            if not operator:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mobile operator not found"
                )

            operator.status = ActivityStatus.ACTIVE
            operator.updated_at = Helpers.utc6dhaka()
            self.db.commit()
            self.db.refresh(operator)

            return GlobalResponse(
                success=True,
                message="Operator activated successfully",
                data={
                    "operator_id": operator.operator_id,
                    "status": operator.status.value
                }
            )

        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
