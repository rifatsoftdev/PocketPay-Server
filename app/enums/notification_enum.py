from enum import Enum


class NotificationType(str, Enum):
    ALERT = "alert"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEFAULT = "default"
    REQUEST = "request"
    BILLPAY = "billpay"
    DONATION = "donation"
    TRANSACTION = "transaction"