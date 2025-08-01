from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime)
    logout_time = Column(DateTime)
    ip_address = Column(String)
    visible = Column(Boolean, default=True)

    user = relationship("User", back_populates="session_logs")
