from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from utils.security import hash_password  # <-- ensure this is present

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    theme_mode = Column(String(20), default="system")
    accent_color = Column(String(20), default="#ffdf00")
    font = Column(String, default="Roboto")
    font_size = Column(Integer, default=12)

    font_treeview = Column(String(50))
    font_treeview_size = Column(Integer)
    font_label = Column(String(50))
    font_label_size = Column(Integer)
    font_button = Column(String(50))
    font_button_size = Column(Integer)
    font_entry = Column(String(50))
    font_entry_size = Column(Integer)

    session_logs = relationship("SessionLog", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

    def set_password(self, raw_password: str):
        self.password_hash = hash_password(raw_password)