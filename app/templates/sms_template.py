class SMSTemplate:
    @staticmethod
    def otp_sms(otp: str):
        return f"Your {otp} is the OTP for PocketPay. Valid for 5 minutes. Please do not share this code with anyone."

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