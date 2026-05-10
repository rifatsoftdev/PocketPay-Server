class PushTemplate:
    @staticmethod
    def transaction_push(title: str, amount: float, status: str = "successful"):
        return {
            "title": title,
            "body": f"Your transaction of {amount} TK was {status}. Tap to see details."
        }

    @staticmethod
    def login_alert_push(ip_address: str):
        return {
            "title": "New Login Detected 🔐",
            "body": f"A new login was detected from IP: {ip_address}. If this wasn't you, please secure your account."
        }

    @staticmethod
    def kyc_update_push(status: str):
        return {
            "title": "KYC Verification Update",
            "body": f"Your KYC verification status has been updated to: {status.upper()}."
        }

    # আপনি চাইলে এখানে আরও প্রোমোশনাল বা কাস্টম অফার টেমপ্লেট যোগ করতে পারেন।