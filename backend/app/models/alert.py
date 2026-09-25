import datetime as dt
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    monitoring_run_id = Column(Integer, ForeignKey("monitoring_runs.id"), nullable=False)

    # UNAUTHORIZED_EXPANSION | PERMITTED_ACTIVITY | INFO
    alert_type = Column(String(50), nullable=False)
    # LOW | MEDIUM | HIGH | CRITICAL
    severity = Column(String(20), nullable=False, default="HIGH")
    message = Column(Text, nullable=False)
    expansion_area_ha = Column(Float, default=0.0)
    geometry = Column(Text, nullable=True)  # GeoJSON of the unauthorized area

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    monitoring_run = relationship("MonitoringRun", back_populates="alerts")
