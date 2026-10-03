"""
Stores the geometries (as GeoJSON text) produced by a monitoring run:
current excavation mask, previous excavation mask, new excavation,
and the unauthorized (outside-boundary) portion.
"""
from sqlalchemy import Column, Integer, ForeignKey, Text, String, Float
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

    # Optional elevation-derived estimate. Historical rows are explicitly unavailable.
    depth_status = Column(String(32), nullable=False, default="UNAVAILABLE", server_default="UNAVAILABLE")
    depth_message = Column(Text, nullable=True)
    mean_depth_m = Column(Float, nullable=True)
    median_depth_m = Column(Float, nullable=True)
    max_depth_m = Column(Float, nullable=True)
    min_depth_m = Column(Float, nullable=True)
    estimated_volume_m3 = Column(Float, nullable=True)
    valid_elevation_samples = Column(Integer, nullable=True)
    elevation_source = Column(String(255), nullable=True)
    depth_method = Column(String(255), nullable=True)
    before_elevation_date = Column(String(20), nullable=True)
    after_elevation_date = Column(String(20), nullable=True)

    monitoring_run = relationship("MonitoringRun", back_populates="excavation_result")
