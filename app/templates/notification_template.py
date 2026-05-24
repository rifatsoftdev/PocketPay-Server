from enum import Enum
from typing import Any

from app.constants import String
from app.templates.email_template import main_structure


class NotificationTemplate:
    @staticmethod
    def _clean(value: Any, default: str = "") -> str:
        if value is None:
            return default
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)

    @staticmethod
    def _money(value: Any) -> str:
        try:
            number = float(value)
            return f"{number:,.2f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return NotificationTemplate._clean(value, "0")

    @staticmethod
    def _normalize(template: str) -> str:
        return NotificationTemplate._clean(template).lower().replace("_", ".").replace("-", ".").replace(" ", ".")

    @staticmethod
    def _email_body(title: str, message: str, name: str = None, details: dict = None, button_text: str = None, button_link: str = None):
        greeting = f"Hello {name}," if name else "Hello,"
        detail_rows = ""

        for key, value in (details or {}).items():
            if value is None or value == "":
                continue
            detail_rows += f"""
                <tr>
                  <td style="padding:8px 0; color:#777777;">{key}</td>
                  <td style="padding:8px 0; color:#333333; text-align:right; font-weight:bold;">{value}</td>
                </tr>
            """

        details_html = f"""
            <table width="100%" style="background-color:#f1f2f6; padding:15px; border-radius:8px; margin:20px 0; font-size:14px;">
              {detail_rows}
            </table>
        """ if detail_rows else ""

        button_html = f"""
            <div style="text-align:center; margin-top:25px;">
              <a href="{button_link}" style="display:inline-block; background-color:#1E88E5; color:#ffffff; text-decoration:none; padding:12px 24px; border-radius:6px; font-size:15px; font-weight:bold;">{button_text}</a>
            </div>
        """ if button_text and button_link else ""

        return main_structure(f"""
          <tr>
            <td style="padding:35px;">
              <h2 style="color:#333333; text-align:center; margin-bottom:20px;">{title}</h2>
              <p style="color:#555555; font-size:16px; line-height:1.5;">{greeting}</p>
              <p style="color:#555555; font-size:16px; line-height:1.5;">{message}</p>
              {details_html}
              {button_html}
              <p style="color:#999999; font-size:13px; margin-top:25px; text-align:center;">
                This is an automated notification from {String.COMPANY_NAME}.
              </p>
            </td>
          </tr>
        """)

    @staticmethod
    def _pack(title: str, push_body: str, sms_body: str = None, email_body: str = None, db_body: str = None):
        sms_body = sms_body or push_body
        email_body = email_body or NotificationTemplate._email_body(title, push_body)
        db_body = db_body or push_body

        return {
            "push": {"title": title, "body": push_body},
            "sms": {"title": title, "body": sms_body},
            "email": {"title": title, "body": email_body},
            "database": {"title": title, "body": db_body},
        }

    @staticmethod
    def fallback(title: str, body: str, email_body: str = None):
        return NotificationTemplate._pack(
            title=title,
            push_body=body,
            sms_body=f"{String.COMPANY_NAME}: {body}",
            email_body=email_body,
            db_body=body,
        )

    @staticmethod
    def resolve(template: str, context: dict = None, title: str = None, body: str = None):
        context = context or {}
        key = NotificationTemplate._normalize(template)

        if not key:
            return NotificationTemplate.fallback(title or "Notification", body or "")

        if key in ["auth.welcome", "welcome"]:
            return NotificationTemplate.welcome(context)
        if key in ["auth.otp", "otp"]:
            return NotificationTemplate.otp(context)
        if key in ["auth.login.alert", "login.alert"]:
            return NotificationTemplate.login_alert(context)
        if key in ["auth.password.reset.request", "password.reset.request"]:
            return NotificationTemplate.password_reset_request(context)
        if key in ["auth.password.reset.success", "password.reset.success"]:
            return NotificationTemplate.password_reset_success(context)
        if key in ["auth.password.changed", "password.changed"]:
            return NotificationTemplate.password_changed(context)
        if key in ["kyc.updated", "kyc.update"]:
            return NotificationTemplate.kyc_update(context)
        if key in ["admin.custom", "custom", "general"]:
            return NotificationTemplate.general(context, title=title, body=body)

        if key.startswith("transaction."):
            return NotificationTemplate.transaction(key.replace("transaction.", "", 1), context)

        return NotificationTemplate.fallback(title or NotificationTemplate._clean(template).title(), body or "")

    @staticmethod
    def welcome(context: dict):
        name = NotificationTemplate._clean(context.get("name"), "there")
        title = f"Welcome to {String.COMPANY_NAME}!"
        body = f"Hello {name}, your account has been successfully set up. Your security is our priority."
        return NotificationTemplate._pack(
            title=title,
            push_body=body,
            sms_body=f"{String.COMPANY_NAME}: Welcome {name}. Your account is ready.",
            email_body=NotificationTemplate._email_body(title, body, name),
        )

    @staticmethod
    def otp(context: dict):
        name = NotificationTemplate._clean(context.get("name"), "there")
        otp = NotificationTemplate._clean(context.get("otp"))
        purpose = NotificationTemplate._clean(context.get("purpose"), "verification")
        title = f"Your {String.COMPANY_NAME} OTP"
        body = f"Hello {name}, your OTP for {purpose} is {otp}. This code is valid for 5 minutes."
        return NotificationTemplate._pack(
            title=title,
            push_body=body,
            sms_body=f"{String.COMPANY_NAME}: Your OTP is {otp}. Valid for 5 minutes. Do not share it.",
            email_body=NotificationTemplate._email_body(
                title,
                f"Use this OTP to complete your {purpose}: {otp}. This code is valid for 5 minutes.",
                name,
                details={"OTP": otp, "Purpose": purpose},
            ),
        )

    @staticmethod
    def login_alert(context: dict):
        name = NotificationTemplate._clean(context.get("name"), "there")
        ip = NotificationTemplate._clean(context.get("ip_address") or context.get("ip"), "unknown")
        title = "New Login Detected"
        body = f"Hello {name}, a new login was detected from IP {ip}. If this wasn't you, please secure your account."
        return NotificationTemplate._pack(
            title=title,
            push_body=body,
            sms_body=f"{String.COMPANY_NAME}: New login from IP {ip}. If this was not you, secure your account.",
            email_body=NotificationTemplate._email_body(title, body, name, details={"IP Address": ip}),
        )

    @staticmethod
    def password_reset_request(context: dict):
        ip = NotificationTemplate._clean(context.get("ip_address") or context.get("ip"), "unknown")
        title = "Reset Password Request Detected"
        body = f"We received a password reset request for your account from IP {ip}."
        return NotificationTemplate._pack(title, body, f"{String.COMPANY_NAME}: Password reset requested from IP {ip}.")

    @staticmethod
    def password_reset_success(context: dict):
        ip = NotificationTemplate._clean(context.get("ip_address") or context.get("ip"), "unknown")
        title = "Password Reset Successful"
        body = f"Your password has been successfully reset from IP {ip}."
        return NotificationTemplate._pack(title, body, f"{String.COMPANY_NAME}: Your password was reset from IP {ip}.")

    @staticmethod
    def password_changed(context: dict):
        ip = NotificationTemplate._clean(context.get("ip_address") or context.get("ip"), "unknown")
        title = "Password Changed"
        body = f"Your password was changed from IP {ip}. If this wasn't you, reset your password immediately."
        return NotificationTemplate._pack(title, body, f"{String.COMPANY_NAME}: Password changed from IP {ip}.")

    @staticmethod
    def kyc_update(context: dict):
        name = NotificationTemplate._clean(context.get("name"), "there")
        status = NotificationTemplate._clean(context.get("status"), "updated").upper()
        reason = NotificationTemplate._clean(context.get("reason") or context.get("rejection_reason"))
        title = "KYC Verification Update"
        body = f"Hello {name}, your KYC verification status is now {status}."
        if reason:
            body = f"{body} Reason: {reason}."
        return NotificationTemplate._pack(
            title,
            body,
            f"{String.COMPANY_NAME}: Your KYC status is {status}.",
            NotificationTemplate._email_body(title, body, name, details={"Status": status, "Reason": reason}),
        )

    @staticmethod
    def general(context: dict, title: str = None, body: str = None):
        title = title or NotificationTemplate._clean(context.get("title"), "Notification")
        message = body or NotificationTemplate._clean(context.get("body") or context.get("message"))
        name = NotificationTemplate._clean(context.get("name"))
        button_text = NotificationTemplate._clean(context.get("button_text"))
        button_link = NotificationTemplate._clean(context.get("button_link"))
        return NotificationTemplate._pack(
            title=title,
            push_body=message,
            sms_body=f"{String.COMPANY_NAME}: {message}",
            email_body=NotificationTemplate._email_body(title, message, name, button_text=button_text, button_link=button_link),
            db_body=message,
        )

    @staticmethod
    def transaction(transaction_type: str, context: dict):
        tx_type = NotificationTemplate._normalize(transaction_type).replace(".", "")
        amount = NotificationTemplate._money(context.get("amount"))
        amount_text = f"{amount} TK"
        receiver = NotificationTemplate._clean(context.get("receiver") or context.get("recipient") or context.get("receiver_account"), "recipient")
        sender = NotificationTemplate._clean(context.get("sender") or context.get("sender_account"), "sender")
        account = NotificationTemplate._clean(context.get("account") or context.get("bill_account") or context.get("number"))
        provider = NotificationTemplate._clean(context.get("provider") or context.get("account_name") or context.get("organization"))
        reference = NotificationTemplate._clean(context.get("reference"))
        service_charge = context.get("service_charge") if "service_charge" in context else context.get("charge")
        total = context.get("total") if "total" in context else context.get("total_deducted")
        txn_id = NotificationTemplate._clean(context.get("transaction_id") or context.get("txn_id"))
        status = NotificationTemplate._clean(context.get("status"), "successful").lower()
        status_label = "successful" if status in ["success", "successful", "completed", "complete"] else status

        details = {
            "Amount": amount_text,
            "Service Charge": f"{NotificationTemplate._money(service_charge)} TK" if service_charge is not None else None,
            "Total Deducted": f"{NotificationTemplate._money(total)} TK" if total is not None else None,
            "Reference": reference if reference and reference.upper() != "N/A" else None,
            "Transaction ID": txn_id,
        }

        if tx_type in ["sendmoney", "sentmoney"]:
            title = "Money Sent Successfully" if status_label == "successful" else f"Money Sent {status_label.title()}"
            body = f"You have sent {amount_text} to {receiver}."
            details["Receiver"] = receiver
        elif tx_type in ["receivemoney", "receivedmoney"]:
            title = "Money Received"
            body = f"You have received {amount_text} from {sender}."
            details["Sender"] = sender
        elif tx_type in ["recharge", "mobilerecharge"]:
            title = "Mobile Recharge Successful" if status_label == "successful" else f"Mobile Recharge {status_label.title()}"
            body = f"Recharge of {amount_text} to {account or receiver} was {status_label}."
            details["Number"] = account or receiver
        elif tx_type == "donation":
            title = "Donation Successful" if status_label == "successful" else f"Donation {status_label.title()}"
            body = f"You have donated {amount_text}{f' to {provider}' if provider else ''}."
            details["Organization"] = provider
        elif tx_type in ["billpay", "paybill"]:
            title = "Pay Bill Successful" if status_label == "successful" else f"Pay Bill {status_label.title()}"
            body = f"You have paid {amount_text}{f' to {provider}' if provider else ''}{f' for account {account}' if account else ''}."
            details["Provider"] = provider
            details["Account"] = account
        elif tx_type in ["devpay", "payment"]:
            title = "Payment Successful" if status_label == "successful" else f"Payment {status_label.title()}"
            body = f"You have paid {amount_text}{f' to {provider or receiver}' if provider or receiver else ''}."
            details["Receiver"] = provider or receiver
        elif tx_type == "deposit":
            title = "Deposit Successful" if status_label == "successful" else f"Deposit {status_label.title()}"
            body = f"{amount_text} has been added to your wallet."
        elif tx_type == "withdraw":
            title = "Withdraw Successful" if status_label == "successful" else f"Withdraw {status_label.title()}"
            body = f"You have withdrawn {amount_text}{f' to {account}' if account else ''}."
            details["Account"] = account
        elif tx_type == "reward":
            title = "Reward Received"
            body = f"You have received a reward of {amount_text}."
        elif tx_type == "cashback":
            title = "Cashback Received"
            body = f"You have received cashback of {amount_text}."
        else:
            title = f"{transaction_type.title()} {status_label.title()}"
            body = f"Your transaction of {amount_text} was {status_label}. Tap to see details."

        extra = []
        if service_charge is not None:
            extra.append(f"Service Charge: {NotificationTemplate._money(service_charge)} TK")
        if total is not None:
            extra.append(f"Total Deducted: {NotificationTemplate._money(total)} TK")
        if reference and reference.upper() != "N/A":
            extra.append(f"Reference: {reference}")

        push_body = f"{body} {'; '.join(extra)}." if extra else body
        sms_body = f"{String.COMPANY_NAME}: {push_body}"

        return NotificationTemplate._pack(
            title=title,
            push_body=push_body,
            sms_body=sms_body,
            email_body=NotificationTemplate._email_body(title, body, details=details),
            db_body=push_body,
        )
