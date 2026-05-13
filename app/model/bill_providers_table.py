from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums import BillCategory, ActivityStatus
from app.utils.helpers import utc6dhaka





class BillProviderTable(Base):
    __tablename__ = "bill_providers"

    id = Column(Integer, autoincrement=True, index=True)
    
    company_id = Column(
        String,
        primary_key=True,
        unique=True,
        nullable=False
    )
    
    category = Column(Enum(BillCategory, native_enum=False), nullable=False)
    
    company_logo = Column(String, nullable=True)
    company_name = Column(String, nullable=False)
    company_api = Column(String, nullable=True)
    company_user_id = Column(String, nullable=True)
    description = Column(String, nullable=False)
    is_gateway = Column(Boolean, default=False)

    min_amount = Column(Numeric(18, 2), nullable=True)
    max_amount = Column(Numeric(18, 2), nullable=True)

    meta_data = Column(JSON, nullable=True)

    status = Column(
        Enum(ActivityStatus),
        default=ActivityStatus.PENDING,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), default=utc6dhaka)
    updated_at = Column(DateTime(timezone=True), onupdate=utc6dhaka)

    # transactions = relationship("TransactionTable", back_populates="bill_provider")
