from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum

from app.core.database import Base
from app.enums.enums import ActivityStatus
from app.utils.helpers import utc6dhaka



class CountryTable(Base):
    __tablename__ = "country_list"

    counrty_id = Column(String, primary_key=True, nullable=False)

    counrty_name = Column(String, unique=True, nullable=False)
    counrty_code = Column(String, nullable=False)  # country dialing code, e.g., +880
    flag_emoji = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    currency_symbol = Column(String, nullable=False)
    status = Column(Enum(ActivityStatus), nullable=False, default=ActivityStatus.PENDING)

    meta_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc6dhaka)
    updated_at = Column(DateTime(timezone=True), onupdate=utc6dhaka)


