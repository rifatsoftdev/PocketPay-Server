
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums import ActivityStatus
from app.utils.helpers import utc6dhaka




class DonationTable(Base):
    __tablename__ = "donation_list"

    organization_id = Column(Integer, primary_key=True, autoincrement=True)
    
    organization_name = Column(String, nullable=False)
    organization_logo = Column(String, nullable=True)
    organization_api = Column(String, nullable=True)
    description = Column(String, nullable=False)

    min_amount = Column(Numeric(18, 2), nullable=True)
    max_amount = Column(Numeric(18, 2), nullable=True)

    meta_data = Column(JSON, nullable=True)

    status = Column(
        Enum(ActivityStatus),
        default=ActivityStatus.ACTIVE,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), default=utc6dhaka)
    updated_at = Column(DateTime(timezone=True), onupdate=utc6dhaka)

    # transactions = relationship("TransactionTable", back_populates="bill_provider")


