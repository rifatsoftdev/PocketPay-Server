from app.constants import String


class SMSTemplate:
    @staticmethod
    def welcome_sms_template(name: str):
        return {
            "title": "Welcome to PocketPay!",
            "body": f"Hello {name}, thank you for joining PocketPay. We're excited to have you on board! Start exploring our services and enjoy seamless transactions."
        }
    
    @staticmethod
    def otp_sms_template(name: str, email: str, otp: str):
        return {
            "title": "Your OTP Code for PocketPay",
            "body": f"Hello {name}, your OTP for PocketPay is {otp}. This code is valid for 5 minutes. Please do not share this code with anyone."
        }

    @staticmethod
    def login_alert_sms_template(name: str, ip_address: str):
        return {
            "title": "New Login Detected 🔐",
            "body": f"Hello {name}, a new login was detected from IP: {ip_address}. If this wasn't you, please secure your account."
        }
    
    @staticmethod
    def kyc_update_sms_template(name: str, status: str):
        return {
            "title": "KYC Verification Update",
            "body": f"Hello {name}, your KYC verification status has been updated to: {status.upper()}."
        }




    @staticmethod
    def cash_in_sms(amount: float, balance: float):
        return f"PocketPay: Cash In of {amount} TK successful. Current balance {balance} TK. Transaction ID: [TXN_ID]."

    @staticmethod
    def cash_out_sms(amount: float, balance: float):
        return f"PocketPay: Cash Out of {amount} TK successful. Current balance {balance} TK. Fee applied. Thank you."

    @staticmethod
    def send_money_sms(amount: float, recipient: str):
        return f"PocketPay: You have successfully sent {amount} TK to {recipient}. Thank you for using PocketPay."

    @staticmethod
    def generic_alert_sms(message: str):
        return f"PocketPay Alert: {message}"

