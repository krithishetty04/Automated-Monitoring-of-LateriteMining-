"""Manually recorded extraction, depth, and restoration updates."""
import datetime as dt

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class SiteUpdate(Base):
    __tablename__ = "site_updates"

    id = Column(Integer, primary_key=True, index=True)
    area_name = Column(String(160), nullable=True)
    tonnes_removed = Column(Float, nullable=True)
    depth_m = Column(Float, nullable=True)
    cover_status = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
