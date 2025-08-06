from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String)
    action = Column(String)
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    visible = Column(Boolean, default=True)

    user = relationship("User", back_populates="audit_logs")
