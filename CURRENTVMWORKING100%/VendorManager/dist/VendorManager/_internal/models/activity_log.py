from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String)
    action = Column(String)
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    visible = Column(Boolean, default=True)

    user = relationship("User", back_populates="activity_logs")