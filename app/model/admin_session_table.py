from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, synonym

from app.core.database import Base
from app.utils.helpers import utc6dhaka


class AdminSessionTable(Base):
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String, ForeignKey("admin_list.admin_id"), index=True)

    session_id = Column(String, unique=True, index=True)

    access_token_hash = Column(String, nullable=True)
    refresh_token_hash = Column(String, nullable=True)
    fcm_token = Column(String, nullable=True)

    device_uuid = Column(String, nullable=True)
    device_id = Column(String, nullable=True)

    device_type = Column(String, nullable=True)
    device_name = Column(String, nullable=True)

    last_ip_address = Column(String, nullable=True)

    is_used = Column(Boolean, default=True)
    # Backward compatibility for code expecting is_active
    is_active = synonym("is_used")
    
    last_seen_at = Column(DateTime(timezone=True), default=utc6dhaka)

    login_at = Column(DateTime(timezone=True), default=utc6dhaka)
    logout_at = Column(DateTime(timezone=True), onupdate=utc6dhaka, nullable=True)


    # Relationship
    admin = relationship(
        "AdminTable",
        back_populates="login_sessions"
    )
