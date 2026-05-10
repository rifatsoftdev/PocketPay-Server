from enum import Enum as PyEnum



class PaymentMethods(str, PyEnum):
    WALLET = "wallet"
    BKASH = "bkash"
    NAGAD = "nagad"
    UPAI = "upai"
    ROCKET = "rocket"
    BANK = "bank"

class BillCategory(str, PyEnum):
    INTERNET = "internet"
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    ECOMMERCE = "ecommerce"
    RENT = "rent"
    FOOD = "food"
    TRAVEL = "travel"
    MERCHANT = "merchant"
    TV = "tv"
    TELEPHONE = "telephone"
    OTHER = "other"


class KYCStatus(str, PyEnum):
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"
    FAILED = "failed"
    DISABLED = "disable"
    REQUIRED = "required"


class ActivityStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


