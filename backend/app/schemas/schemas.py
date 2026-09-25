"""
Pydantic response/request models used by the API layer.
"""
from typing import Optional, Any, Dict, Literal
import datetime as dt
from pydantic import BaseModel


# ---------------- Quarry ----------------
class QuarryOut(BaseModel):
    id: int
    name: str
    area_ha: float
    geometry_geojson: str

    class Config:
        from_attributes = True


# ---------------- Excavation result ----------------
class ExcavationResultOut(BaseModel):
    id: int
    current_excavation_geojson: Optional[str] = None
    previous_excavation_geojson: Optional[str] = None
    new_excavation_geojson: Optional[str] = None
    unauthorized_expansion_geojson: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- Monitoring run ----------------
class MonitoringRunOut(BaseModel):
    id: int
    quarry_id: int
    image_date: str
    previous_image_date: Optional[str] = None
    cloud_percentage: Optional[float] = None
    current_excavation_area_ha: float
    previous_excavation_area_ha: float
    new_excavation_area_ha: float
    inside_area_ha: float
    outside_area_ha: float
    status: str
    source: str
    created_at: dt.datetime
    excavation_result: Optional[ExcavationResultOut] = None

    class Config:
        from_attributes = True


class MonitoringRunSummary(BaseModel):
    """Lightweight row used in the history table."""
    id: int
    image_date: str
    previous_image_date: Optional[str] = None
    current_excavation_area_ha: float
    new_excavation_area_ha: float
    outside_area_ha: float
    status: str
    source: str

    class Config:
        from_attributes = True


class MonitoringRunRequest(BaseModel):
    """Body for POST /api/monitoring/run"""
    mode: Literal["real"] = "real"


# ---------------- Alerts ----------------
class AlertOut(BaseModel):
    id: int
    monitoring_run_id: int
    alert_type: str
    severity: str
    message: str
    expansion_area_ha: float
    geometry: Optional[str] = None
    is_read: bool
    created_at: dt.datetime

    class Config:
        from_attributes = True


class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list = []
