
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone
from .database import Base

class FileStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DELETED = "deleted"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    sent_files = relationship("File", foreign_keys="[File.sender_id]", back_populates="sender")
    received_files = relationship("File", foreign_keys="[File.recipient_id]", back_populates="recipient")
    
    sent_messages = relationship("Message", foreign_keys="[Message.sender_id]", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="[Message.recipient_id]", back_populates="recipient")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    uuid_filename = Column(String, unique=True, index=True) # Name on disk
    display_filename = Column(String) # Original sanitized name
    
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)
    downloaded_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    status = Column(String, default=FileStatus.ACTIVE) # Storing Enum as string for simpler SQLite handling

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_files")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_files")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
