from fastapi import BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session
from decimal import Decimal

from app.constants import AnsiColor, String
from app.schema import GlobalResponse, DonationOut, DonationsRequest, DonationOrgRequest, DonationOrgRemoveRequest
from app.enums import ActivityStatus, PaymentMethods, NotificationType, TransactionDirection, TransactionStatus, TransactionType
from app.model import TransactionTable, WalletTable, DonationTable, AdminTable, UserTable
from app.utils import Generators, Helpers, Token

from app.services.wallet.wallet_service import WalletService, ServiceChargeData
from app.services.auth.user_verification import UserVerificationService
from app.services.notification.noticication_services import NotificationServices, NotificationData



class DonationServices(WalletService):
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

    def _verify_admin_request(self):
        access_token = Helpers.authorization(self.authorization)
        payload = Token().decode_token(access_token)
        if not payload or payload.get("type") != "access" or not payload.get("admin_id"):
            raise HTTPException(status_code=401, detail=String.INVALID_TOKEN)

        admin = self.db.query(AdminTable).filter(
            AdminTable.admin_id == payload.get("admin_id"),
            AdminTable.is_active == True
        ).first()

        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")

        return admin

    def get_donations(self) -> GlobalResponse:
        try:
            donate_list = self.db.query(DonationTable).filter(
                DonationTable.status == ActivityStatus.ACTIVE
            ).all()
            
            donate_list_out = [DonationOut.model_validate(p) for p in donate_list]

            return GlobalResponse(
                success=True,
                message="Donations fetched successfully",
                data={"donations": donate_list_out}
            )
        except HTTPException:
            raise

        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def make_donation(self, payload: DonationsRequest) -> GlobalResponse:
        try:
            user_verification_service = UserVerificationService(self.db)
            user: UserTable = user_verification_service.verify_user(
                user_id=payload.user_id,
                access_token=payload.access_token,
                device_id=payload.device_id,
                device_uuid=payload.device_uuid,
                password=payload.user_password
            )

            organization = self.db.query(DonationTable).filter(
                DonationTable.organization_id == payload.organization_id,
                DonationTable.status == ActivityStatus.ACTIVE
            ).first()
            
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")

            wallet = self.db.query(WalletTable).filter(
                WalletTable.user_id == user.user_id
            ).with_for_update().first()
            
            if not wallet:
                raise HTTPException(status_code=404, detail=String.WALLET_NOT_FOUND)

            charge: ServiceChargeData = self.service_charge(payload.amount)

            if wallet.balance < charge.total:
                raise HTTPException(status_code=400, detail=String.INSUFFICIENT_BALANCE)

            transaction_id = Generators.generate_transaction_id()
            sender_account = (user.country_code + user.phone_number) if user.phone_number else (user.email_address or user.user_id)

            transaction = TransactionTable(
                transaction_id=transaction_id,
                transaction_type=TransactionType.DONATION,
                method=PaymentMethods.WALLET,
                sender_user_id=user.user_id,
                sender_account=sender_account,
                receiver_account=None,
                receiver_user_id=None,
                account_id=str(organization.organization_id),
                account_name=organization.organization_name,
                currency=wallet.currency or "BDT",
                amount=charge.amount,
                service_charge=charge.charge,
                reference=payload.refarence or "N/A",
                direction=TransactionDirection.OUT,
                status=TransactionStatus.SUCCESS
            )
            self.db.add(transaction)
            self.db.flush()

            wallet.balance -= charge.total
            wallet.last_updated = Helpers.utc6dhaka()

            try:
                notificationServices = NotificationServices(
                    db=self.db,
                    background_tasks=self.background_tasks
                )

                notificationServices.send_notification(
                    NotificationData(
                        user_id=user.user_id,
                        title="Donation Successful",
                        body=f"You have successfully donated to {organization.organization_name}. Amount: {payload.amount} TK. Total Deducted: {charge.total} TK.",
                        noty_type=NotificationType.TRANSACTION,
                    )
                )
            except:
                pass

            self.db.commit()
            return GlobalResponse(success=True, message="Donation successful", data={})

        except HTTPException:
            self.db.rollback()
            raise
        
        except Exception as e:
            self.db.rollback()
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def organization_request(self, payload: DonationOrgRequest) -> GlobalResponse:
        try:
            is_user_request = all([
                payload.user_id,
                payload.access_token,
                payload.android_id,
                payload.android_uuid
            ])

            if is_user_request:
                user_verification_service = UserVerificationService(self.db)
                user_verification_service.verify_user(
                    user_id=payload.user_id,
                    access_token=payload.access_token,
                    device_id=payload.android_id,
                    device_uuid=payload.android_uuid
                )
                status = ActivityStatus.PENDING
            else:
                self._verify_admin_request()
                status = ActivityStatus.ACTIVE

            new_org = DonationTable(
                organization_name=payload.organization_name,
                description=payload.description,
                organization_logo=payload.organization_logo,
                organization_api=payload.organization_api,
                min_amount=payload.min_amount,
                max_amount=payload.max_amount,
                meta_data=payload.meta_data,
                status=status
            )
            self.db.add(new_org)
            self.db.commit()
            message = "Donation organization added successfully" if status == ActivityStatus.ACTIVE else "Organization request submitted"
            return GlobalResponse(
                success=True,
                message=message,
                data={
                    "organization_id": new_org.organization_id,
                    "status": status.value
                }
            )
        except HTTPException: raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)

    def organization_remove_request(self, payload: DonationOrgRemoveRequest) -> GlobalResponse:
        try:
            is_user_request = all([
                payload.user_id,
                payload.access_token,
                payload.android_id,
                payload.android_uuid
            ])

            if is_user_request:
                user_verification_service = UserVerificationService(self.db)
                user_verification_service.verify_user(
                    user_id=payload.user_id,
                    access_token=payload.access_token,
                    device_id=payload.android_id,
                    device_uuid=payload.android_uuid
                )
                new_status = ActivityStatus.PENDING
            else:
                self._verify_admin_request()
                new_status = ActivityStatus.INACTIVE

            org = self.db.query(DonationTable).filter(DonationTable.organization_id == payload.organization_id).first()
            if not org:
                raise HTTPException(status_code=404, detail="Organization not found")

            org.status = new_status
            self.db.commit()
            message = "Organization removed successfully" if new_status == ActivityStatus.INACTIVE else "Removal request submitted"
            return GlobalResponse(success=True, message=message, data={})
        except HTTPException: raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=String.SERVER_ERROR)
