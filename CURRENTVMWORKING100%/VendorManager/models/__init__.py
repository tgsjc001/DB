# models/__init__.py
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Import models
from .user import User
from .audit_log import AuditLog
from .vendor import Vendor
from .session_log import SessionLog
from .activity_log import ActivityLog
from .user_settings import UserSettings

# Relationship bindings (must come after imports)
User.audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
AuditLog.user = relationship("User", back_populates="audit_logs")

User.activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
ActivityLog.user = relationship("User", back_populates="activity_logs")

User.session_logs = relationship("SessionLog", back_populates="user", cascade="all, delete-orphan")
SessionLog.user = relationship("User", back_populates="session_logs")

User.settings = relationship("UserSettings", back_populates="user", cascade="all, delete-orphan")
UserSettings.user = relationship("User", back_populates="settings")