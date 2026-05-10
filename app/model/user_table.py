from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums.user_enum import Gender, UserType
from app.utils.helpers import utc6dhaka




class UserTable(Base):
    __tablename__ = "user_list"

    user_id = Column(String, primary_key=True, unique=True, index=True)

    full_name = Column(String(30), nullable=False)
    email_address = Column(String(30), unique=True, index=True, nullable=False)

    country_code = Column(String(4), nullable=True)
    phone_number = Column(String(14), unique=True, index=True, nullable=True)
    
    password_hash = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)

    phone_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    link_google = Column(String, nullable=True)

    user_type = Column(Enum(UserType), default=UserType.NORMAL)
    user_gender = Column(Enum(Gender), default=Gender.UNDIFINED)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc6dhaka)
    updated_at = Column(DateTime(timezone=True), onupdate=utc6dhaka)


    # Relationship
    wallet = relationship(
        "WalletTable",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    settings = relationship(
        "SettingsTable",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    sent_transactions = relationship(
        "TransactionTable",
        foreign_keys="TransactionTable.sender_user_id",
        back_populates="sender"
    )

    received_transactions = relationship(
        "TransactionTable",
        foreign_keys="TransactionTable.receiver_user_id",
        back_populates="receiver"
    )

    notifications = relationship(
        "NotificationTable",
        foreign_keys="NotificationTable.target_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
