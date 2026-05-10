from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums.enums import KYCStatus
from app.utils.helpers import utc6dhaka



class SettingsTable(Base):
    __tablename__ = "user_settings"

    user_id = Column(String, ForeignKey("user_list.user_id"), primary_key=True)

    # Settins
    allow_notifications = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=False)
    country = Column(String, default="BD")
    language = Column(String, default="en")

    # Secrutry
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    two_factor = Column(JSON, nullable=True)

    biometric_enabled = Column(Boolean, nullable=False, default=False)
    biometric_secret = Column(String, nullable=True)
    
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    kyc_verified_by = Column(String, nullable=True)  # admin_id / system
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Account Deactived
    account_locked = Column(Boolean, default=False)
    
    updated_at = Column(DateTime(timezone=True), onupdate=utc6dhaka)
    created_at = Column(DateTime(timezone=True), default=utc6dhaka)

    user = relationship(
        "UserTable",
        back_populates="settings"
    )
    