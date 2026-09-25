"""
Official permitted quarry boundary.
The geometry is stored as GeoJSON text (works without PostGIS).
"""
import datetime as dt
from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.database import Base


class Quarry(Base):
    __tablename__ = "quarry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="Official Quarry")
    # GeoJSON Polygon (EPSG:4326) as text
    geometry_geojson = Column(Text, nullable=False)
    area_ha = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
