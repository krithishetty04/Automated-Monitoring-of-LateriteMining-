"""
Simple users/admins table.
Not wired to auth endpoints yet (kept minimal per the request), but the
table exists so it can be extended with login/JWT later.
"""
import datetime as dt
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
