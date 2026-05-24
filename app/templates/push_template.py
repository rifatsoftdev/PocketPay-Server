from enum import Enum
from typing import Any

from app.constants import String


class PushTemplate:
    @staticmethod
    def welcome_push_template(name: str):
        return {
            "title": "Welcome to PocketPay!",
            "body": f"Hello {name}, thank you for joining us. We're excited to have you on board!"
        }
    
    @staticmethod
    def otp_push_template(name: str, email: str, otp: str):
        return {
            "title": "Your OTP Code",
            "body": f"Hello {name}, your OTP for PocketPay is {otp}. This code is valid for 5 minutes. Please do not share this code with anyone."
        }


    @staticmethod
    def login_alert_push_template(name: str, ip_address: str):
        return {
            "title": "New Login Detected 🔐",
            "body": f"Hello {name}, a new login was detected from IP: {ip_address}. If this wasn't you, please secure your account."
        }

    @staticmethod
    def kyc_update_push_template(name: str, status: str):
        return {
            "title": "KYC Verification Update",
            "body": f"Hello {name}, your KYC verification status has been updated to: {status.upper()}."
        }

    


    @staticmethod
    def transaction_push_template(
        transaction_type: str,
        amount: float,
        status: str = "success",
        **kwargs: Any
    ):
        """
        Build title and body for any transaction push notification.

        Example:
            PushTemplate.transaction_push_template(
                "sendmoney",
                amount=500,
                receiver="+8801XXXXXXXXX",
                service_charge=5,
                total=505,
                reference="Dinner"
            )
        """
        def clean(value: Any, default: str = "") -> str:
            if value is None:
                return default
            if isinstance(value, Enum):
                return str(value.value)
            return str(value)

        def money(value: Any) -> str:
            try:
                number = float(value)
                return f"{number:,.2f}".rstrip("0").rstrip(".")
            except (TypeError, ValueError):
                return clean(value, "0")

        tx_type = clean(transaction_type).lower().replace("_", "").replace("-", "").replace(" ", "")
        status_text = clean(status, "success").lower()
        is_success = status_text in ["success", "successful", "completed", "complete"]
        status_label = "Successful" if is_success else status_text.title()
        sent_status_label = "Successfully" if is_success else status_label
        amount_text = f"{money(amount)} TK"

        receiver = clean(kwargs.get("receiver") or kwargs.get("recipient") or kwargs.get("receiver_account"), "recipient")
        sender = clean(kwargs.get("sender") or kwargs.get("sender_account"), "sender")
        account = clean(kwargs.get("account") or kwargs.get("bill_account") or kwargs.get("number"))
        provider = clean(kwargs.get("provider") or kwargs.get("account_name") or kwargs.get("organization"))
        reference = clean(kwargs.get("reference"))
        service_charge = kwargs.get("service_charge") or kwargs.get("charge")
        total = kwargs.get("total") or kwargs.get("total_deducted")

        details = []
        if service_charge is not None:
            details.append(f"Service Charge: {money(service_charge)} TK")
        if total is not None:
            details.append(f"Total Deducted: {money(total)} TK")
        if reference and reference.upper() != "N/A":
            details.append(f"Reference: {reference}")

        suffix = f" {'; '.join(details)}." if details else ""

        templates = {
            "sendmoney": {
                "title": f"Money Sent {sent_status_label}",
                "body": f"You have sent {amount_text} to {receiver}.{suffix}"
            },
            "sentmoney": {
                "title": f"Money Sent {sent_status_label}",
                "body": f"You have sent {amount_text} to {receiver}.{suffix}"
            },
            "receivemoney": {
                "title": "Money Received",
                "body": f"You have received {amount_text} from {sender}.{suffix}"
            },
            "receivedmoney": {
                "title": "Money Received",
                "body": f"You have received {amount_text} from {sender}.{suffix}"
            },
            "recharge": {
                "title": f"Mobile Recharge {status_label}",
                "body": f"Recharge of {amount_text} to {account or receiver} was {status_label.lower()}.{suffix}"
            },
            "mobilerecharge": {
                "title": f"Mobile Recharge {status_label}",
                "body": f"Recharge of {amount_text} to {account or receiver} was {status_label.lower()}.{suffix}"
            },
            "donation": {
                "title": f"Donation {status_label}",
                "body": f"You have donated {amount_text}{f' to {provider}' if provider else ''}.{suffix}"
            },
            "billpay": {
                "title": f"Pay Bill {status_label}",
                "body": f"You have paid {amount_text}{f' to {provider}' if provider else ''}{f' for account {account}' if account else ''}.{suffix}"
            },
            "paybill": {
                "title": f"Pay Bill {status_label}",
                "body": f"You have paid {amount_text}{f' to {provider}' if provider else ''}{f' for account {account}' if account else ''}.{suffix}"
            },
            "deposit": {
                "title": f"Deposit {status_label}",
                "body": f"{amount_text} has been added to your wallet.{suffix}"
            },
            "withdraw": {
                "title": f"Withdraw {status_label}",
                "body": f"You have withdrawn {amount_text}{f' to {account}' if account else ''}.{suffix}"
            },
            "reward": {
                "title": f"Reward {status_label}",
                "body": f"You have received a reward of {amount_text}.{suffix}"
            },
            "cashback": {
                "title": f"Cashback {status_label}",
                "body": f"You have received cashback of {amount_text}.{suffix}"
            },
        }

        return templates.get(tx_type, {
            "title": f"{clean(transaction_type).title()} {status_label}",
            "body": f"Your transaction of {amount_text} was {status_label.lower()}. Tap to see details."
        })
