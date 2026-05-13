from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Numeric, JSON
from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.transactions_enum import TransactionType, TransactionStatus, TransactionDirection
from app.enums import PaymentMethods
from app.utils.helpers import utc6dhaka


class TransactionTable(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String, unique=True, primary_key=True, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    method = Column(Enum(PaymentMethods), nullable=False)

    # transaction creator
    sender_user_id = Column(String, ForeignKey("user_list.user_id"), nullable=False)
    sender_account = Column(String, nullable=False)

    # only for sendmoney
    receiver_user_id = Column(String, ForeignKey("user_list.user_id"), nullable=True)
    receiver_account = Column(String, nullable=True)
    
    # only for paybill, recharge, donation
    account_id = Column(String, nullable=True)
    account_name = Column(String, nullable=True)

    currency = Column(String(3), default="BDT")
    amount = Column(Numeric(18, 2), nullable=False)
    service_charge = Column(Numeric(18, 2), default=0)
    reference = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)

    direction = Column(Enum(TransactionDirection), nullable=False)   # IN / OUT
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)

    created_at = Column(DateTime(timezone=True), default=utc6dhaka)
    updated_at = Column(DateTime(timezone=True), default=utc6dhaka)

    # Relationship
    sender = relationship(
        "UserTable",
        foreign_keys=[sender_user_id],
        back_populates="sent_transactions"
    )

    receiver = relationship(
        "UserTable",
        foreign_keys=[receiver_user_id],
        back_populates="received_transactions"
    )

    # Bill provider
    # bill_provider = relationship("BillProviderTable", back_populates="transactions")