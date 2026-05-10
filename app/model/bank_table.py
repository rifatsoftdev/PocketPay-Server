from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums.enums import BillCategory, ActivityStatus
from app.utils.helpers import utc6dhaka





class BankTable(Base):
    __tablename__ = "bank_list"

    bank_id = Column(String, primary_key=True)

    bank_logo = Column(String, nullable=True)
    bank_name = Column(String, nullable=False)
    bank_api = Column(String, nullable=True)
    description = Column(String, nullable=False)
    is_gateway = Column(Boolean, default=False)

    country_code = Column(String, nullable=False)
    country_name = Column(String, nullable=False)
    meta_data = Column(JSON, nullable=True)

    status = Column(Enum(ActivityStatus), default=ActivityStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=utc6dhaka)
    updated_at = Column(DateTime(timezone=True), onupdate=utc6dhaka)

