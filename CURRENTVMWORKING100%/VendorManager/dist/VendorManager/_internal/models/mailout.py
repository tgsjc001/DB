from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Mailout(Base):
	__tablename__ = 'mailouts'

	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(255), nullable=False)
	address = Column(String(255), nullable=False)
	city = Column(String(100), nullable=False)
	state = Column(String(2), nullable=False)
	zip_code = Column(String(10), nullable=False)
	phone = Column(String(20), nullable=True)
	email = Column(String(255), nullable=True)
	created_date = Column(DateTime, default=datetime.utcnow)

	def __repr__(self):
		return f"<Mailout(id={self.id}, name='{self.name}', city='{self.city}')>"