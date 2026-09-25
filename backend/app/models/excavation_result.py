"""
Stores the geometries (as GeoJSON text) produced by a monitoring run:
current excavation mask, previous excavation mask, new excavation,
and the unauthorized (outside-boundary) portion.
"""
from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ExcavationResult(Base):
    __tablename__ = "excavation_results"

    id = Column(Integer, primary_key=True, index=True)
    monitoring_run_id = Column(Integer, ForeignKey("monitoring_runs.id"), nullable=False)

    current_excavation_geojson = Column(Text, nullable=True)
    previous_excavation_geojson = Column(Text, nullable=True)
    new_excavation_geojson = Column(Text, nullable=True)
    unauthorized_expansion_geojson = Column(Text, nullable=True)

    monitoring_run = relationship("MonitoringRun", back_populates="excavation_result")
