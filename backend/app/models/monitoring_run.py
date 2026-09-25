"""
One row per weekly (or manually-triggered) monitoring execution.
"""
import datetime as dt
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MonitoringRun(Base):
    __tablename__ = "monitoring_runs"

    id = Column(Integer, primary_key=True, index=True)
    quarry_id = Column(Integer, ForeignKey("quarry.id"), nullable=False)

    image_date = Column(String(20), nullable=False)          # e.g. "2026-08-07"
    previous_image_date = Column(String(20), nullable=True)
    cloud_percentage = Column(Float, nullable=True)

    current_excavation_area_ha = Column(Float, default=0.0)
    previous_excavation_area_ha = Column(Float, default=0.0)
    new_excavation_area_ha = Column(Float, default=0.0)
    inside_area_ha = Column(Float, default=0.0)
    outside_area_ha = Column(Float, default=0.0)

    # BASELINE | SAFE | PERMITTED | ALERT | ERROR
    status = Column(String(20), nullable=False, default="SAFE")

    created_at = Column(DateTime, default=dt.datetime.utcnow)

    excavation_result = relationship(
        "ExcavationResult", back_populates="monitoring_run", uselist=False,
        cascade="all, delete-orphan"
    )
    alerts = relationship("Alert", back_populates="monitoring_run", cascade="all, delete-orphan")

    @property
    def source(self) -> str:
        """Derive the acquisition source from the real monitoring source."""
        return "Sentinel-1 SAR" if self.cloud_percentage is None else "Sentinel-2 Optical"
