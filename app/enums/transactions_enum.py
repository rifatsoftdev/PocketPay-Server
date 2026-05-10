from enum import Enum


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    SENDMONEY = "sendmoney"
    DEVPAY = "devpay"
    BILLPAY = "billpay"
    RECHARGE = "recharge"
    DONATION = "donation"
    REWARD = "reward"
    CASHBACK = "cashback"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"



class TransactionDirection(str, Enum):
    IN = "in"
    OUT = "out"
