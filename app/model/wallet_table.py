from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func

from app.core.database import Base
# from app.model.user_table import UserTable
from app.utils.helpers import utc6dhaka



class WalletTable(Base):
    __tablename__ = "user_wallet"
    
    user_id = Column(String, ForeignKey("user_list.user_id"), primary_key=True)

    currency = Column(String(3), default="BDT")
    balance = Column(Numeric(18, 2), default=0)

    total_debits = Column(Numeric(18, 2), default=0)
    total_credits = Column(Numeric(18, 2), default=0)

    last_updated = Column(DateTime(timezone=True), default=utc6dhaka, onupdate=utc6dhaka)

    # relationship
    user = relationship("UserTable", back_populates="wallet", cascade="all, delete-orphan", single_parent=True)
