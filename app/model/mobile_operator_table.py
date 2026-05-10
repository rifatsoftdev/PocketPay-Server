from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums.enums import ActivityStatus
from app.utils.helpers import utc6dhaka




class MobileOperatorTable(Base):
    __tablename__ = "mobile_operator"

    operator_id = Column(String, primary_key=True, nullable=False)

    operator_name = Column(String, nullable=False)        # operator name
    country_code = Column(String(4), ForeignKey("country_list.counrty_code"), nullable=False)
    logo_url = Column(String, nullable=True)     # Optional, for UI
    status = Column(Enum(ActivityStatus), default=ActivityStatus.PENDING, nullable=False)
    operator_api = Column(String, nullable=True)

    meta_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc6dhaka)
    updated_at = Column(DateTime(timezone=True), default=utc6dhaka, onupdate=utc6dhaka)
    
    country = relationship("CountryTable", backref="operators")
