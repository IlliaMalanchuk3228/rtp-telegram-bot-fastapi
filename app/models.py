from sqlalchemy import BigInteger, Column, Integer, String, DateTime, func
from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, index=True, nullable=True)
    subscribe_date = Column(DateTime(timezone=True), server_default=func.now())
