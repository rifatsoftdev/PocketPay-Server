from typing import Optional
from fastapi import BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session
from decimal import Decimal

from app.constants import AnsiColor, String
from app.enums import ActivityStatus, BillCategory, PaymentMethods, NotificationType, TransactionDirection, TransactionStatus, TransactionType
from app.model import BillProviderTable, TransactionTable, WalletTable
from app.schema import (
    PayBillRequest, 
    BillProviderOut,
    BillTransactionDetailsRequest, 
    BillProviderCreateRequest,
    GlobalResponse
)
from app.utils import Generators, Helpers

from app.services.wallet.wallet_service import WalletService, ServiceChargeData
from app.services.auth.user_verification import UserVerificationService
from app.services.notification.noticication_services import NotificationServices, NotificationData



class BillServices(WalletService):
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

    def get_bill_providers(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> GlobalResponse:
        try:
            Helpers.authorization(self.authorization)

            query = self.db.query(BillProviderTable)

            if status:
                try:
                    status_enum = ActivityStatus(status.lower())
                    query = query.filter(BillProviderTable.status == status_enum)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid status")
            else:
                query = query.filter(BillProviderTable.status == ActivityStatus.ACTIVE)

            if category:
                try:
                    category_enum = BillCategory(category.lower())
                    query = query.filter(BillProviderTable.category == category_enum)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid bill category")

            if search:
                query = query.filter(BillProviderTable.company_name.ilike(f"%{search}%"))

            total = query.count()
            offset = (page - 1) * limit
            providers = query.order_by(BillProviderTable.company_name).offset(offset).limit(limit).all()

            if not providers:
                raise HTTPException(status_code=404, detail="Bill categories not found")

            providers_out = [BillProviderOut.from_orm(p) for p in providers]

            return GlobalResponse(
                success=True,
                message="Bill categories fetched successfully",
                data={"bill_categories": providers_out},
                pagination={
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit
                }
            )
        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def get_bill_categories(self, category: str) -> GlobalResponse:
        try:
            try:
                category_enum = BillCategory(category.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid bill category")

            bill_categories = self.db.query(BillProviderTable).filter(
                BillProviderTable.category == category_enum,
                BillProviderTable.status == ActivityStatus.ACTIVE
            ).all()

            if not bill_categories:
                raise HTTPException(status_code=404, detail="Bill categories not found")

            providers_out = [BillProviderOut.from_orm(p) for p in bill_categories]

            return GlobalResponse(
                success=True,
                message="Bill categories fetched successfully",
                data={"bill_categories": providers_out}
            )
        except HTTPException: raise
        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
    
    def bill_transaction_details(self, payload: BillTransactionDetailsRequest) -> GlobalResponse:
        try:
            user_verification_service = UserVerificationService(self.db)
            user = user_verification_service.verify_user(
                user_id=payload.user_id, access_token=payload.access_token,
                device_id=payload.android_id, device_uuid=payload.android_uuid, password=None
            )

            tx = self.db.query(TransactionTable).filter(
                TransactionTable.transaction_id == payload.transaction_id,
                TransactionTable.sender_user_id == user.user_id,
                TransactionTable.transaction_type == TransactionType.BILLPAY
            ).first()

            if not tx: raise HTTPException(status_code=404, detail="Transaction not found")

            return GlobalResponse(
                success=True, message="Transaction fetched successfully",
                data={
                    "transaction_id": tx.transaction_id, "company_id": tx.account_id,
                    "company_name": tx.account_name, "amount": float(tx.amount),
                    "service_charge": float(tx.service_charge or 0),
                    "total_deducted": float((tx.amount or 0) + (tx.service_charge or 0)),
                    "currency": tx.currency, "status": str(tx.status),
                    "reference": tx.reference, "created_at": tx.created_at
                }
            )
        except HTTPException: raise
        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def pay_bill(
        self,
        request: PayBillRequest
    ) -> GlobalResponse:
        try:
            from app.services.wallet.wallet_service import WalletService
            amount = Decimal(str(request.amount))
            reference = request.reference if request.reference else "N/A"

            if amount <= 0:
                raise HTTPException(status_code=400, detail="Amount must be greater than zero")

            try:
                category = BillCategory(str(request.category).lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid bill category")

            try:
                company_id = int(request.company_id)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Invalid company id")

            user_verification_service = UserVerificationService(self.db)
            user = user_verification_service.verify_user(
                user_id=request.user_id,
                access_token=request.access_token,
                android_id=request.android_id,
                android_uuid=request.android_uuid,
                password=request.user_password,
                advance_check=True
            )

            provider = self.db.query(BillProviderTable).filter(
                BillProviderTable.company_id == company_id,
                BillProviderTable.category == category,
                BillProviderTable.status == ActivityStatus.ACTIVE
            ).first()

            if not provider:
                raise HTTPException(status_code=404, detail="Bill provider not found")

            if provider.min_amount is not None and amount < provider.min_amount:
                raise HTTPException(status_code=400, detail=f"Minimum bill amount is {provider.min_amount}")

            if provider.max_amount is not None and amount > provider.max_amount:
                raise HTTPException(status_code=400, detail=f"Maximum bill amount is {provider.max_amount}")

            wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == user.user_id
            ).with_for_update().first()

            if not wallet:
                raise HTTPException(status_code=404, detail=String.WALLET_NOT_FOUND)

            charge: ServiceChargeData = WalletService.service_charge(amount)

            if wallet.balance < charge.total:
                raise HTTPException(status_code=400, detail=String.INSUFFICIENT_BALANCE)

            transaction_id = Generators.generate_transaction_id()
            sender_account = (
                f"{user.country_code or ''}{user.phone_number}"
                if user.phone_number
                else (user.email_address or user.user_id)
            )

            transaction = TransactionTable(
                transaction_id=transaction_id,
                transaction_type=TransactionType.BILLPAY,
                method=PaymentMethods.WALLET,
                sender_user_id=user.user_id,
                sender_account=sender_account,
                receiver_account=request.bill_account,
                receiver_user_id=None,
                account_id=str(provider.company_id),
                account_name=provider.company_name,
                currency=wallet.currency or "BDT",
                amount=charge.amount,
                service_charge=charge.charge,
                reference=reference,
                meta_data={
                    "bill_account": request.bill_account,
                    "bill_category": category.value,
                    "provider_logo": provider.company_logo
                },
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

                notificationServices.send_notification(
                    NotificationData(
                        user_id=user.user_id,
                        title="Pay Bill Successful",
                        short_body=f"You have successfully paid {provider.company_name} bill for account {request.bill_account} with {charge.amount} TK. Service Charge: {charge.charge} TK. Total Deducted: {charge.total} TK.",
                        body=None,
                        noty_type=NotificationType.BILLPAY,
                    )
                )

            except Exception as e:
                print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     Notification failed: {e}")

            self.db.commit()
            self.db.refresh(transaction)
            self.db.refresh(wallet)

            return GlobalResponse(
                success=True,
                message="Bill paid successfully",
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

    def add_bill_provider(self, request: BillProviderCreateRequest) -> GlobalResponse:
        try:
            user_verification_service = UserVerificationService(self.db)
            user = user_verification_service.verify_user(
                user_id=request.user_id,
                access_token=request.access_token,
                device_id=request.device_id,
                device_uuid=request.device_uuid,
                password=request.user_password
            )

            try:
                category = BillCategory(request.category.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid bill category")

            existing = self.db.query(BillProviderTable).filter(BillProviderTable.company_name == request.company_name).first()
            if existing: raise HTTPException(status_code=400, detail="Company Name already exists")

            if request.min_amount is not None and request.max_amount is not None:
                if request.min_amount > request.max_amount:
                    raise HTTPException(status_code=400, detail="min_amount cannot be greater than max_amount")

            new_provider = BillProviderTable(
                category=category, company_logo=request.company_logo,
                company_name=request.company_name, company_api=request.company_api,
                company_user_id=request.company_user_id, description=request.description,
                min_amount=request.min_amount, max_amount=request.max_amount,
                meta_data={
                    "request_user": {
                        "user_id": user.user_id, "phone": user.phone_number,
                        "email": user.email_address, "name": user.full_name
                    }
                }
            )
            self.db.add(new_provider)
            self.db.flush()

            try:
                notificationServices = NotificationServices(
                    db=self.db,
                    background_tasks=self.background_tasks
                )

                notificationServices.send_notification(
                    NotificationData(
                        user_id=user.user_id,
                        title="Bill Provider Request Received",
                        body=f"You have requested to become a bill provider. The request was successful. Wait for Bilal ID {new_provider.company_id} to be activated.",
                        noty_type=NotificationType.REQUEST,
                    )
                )

            except Exception as e:
                print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     Notification failed: {e}")

            self.db.commit()
            self.db.refresh(new_provider)

            return GlobalResponse(
                success=True,
                message="Bill provider added successfully",
                data={}
            )

        except HTTPException: raise
        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)


