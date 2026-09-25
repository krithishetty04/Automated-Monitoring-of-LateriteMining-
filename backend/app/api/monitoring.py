from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.monitoring_run import MonitoringRun
from app.schemas.schemas import MonitoringRunOut, MonitoringRunSummary, MonitoringRunRequest, FeatureCollection
from app.services.monitoring import run_monitoring
import json

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.post("/run", response_model=MonitoringRunOut)
def trigger_monitoring_run(payload: MonitoringRunRequest, db: Session = Depends(get_db)):
    """Manually trigger a live monitoring run against the real Earth Engine workflow."""
    try:
        run = run_monitoring(db, mode=payload.mode)
        return run
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/latest", response_model=MonitoringRunOut)
def get_latest_run(db: Session = Depends(get_db)):
    run = db.query(MonitoringRun).order_by(MonitoringRun.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No monitoring runs yet")
    return run


@router.get("/history", response_model=List[MonitoringRunSummary])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    runs = (
        db.query(MonitoringRun)
        .order_by(MonitoringRun.created_at.asc())
        .limit(limit)
        .all()
    )
    return runs


@router.get("/{run_id}", response_model=MonitoringRunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(MonitoringRun).filter(MonitoringRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Monitoring run not found")
    return run


@router.get("/{run_id}/geojson")
def get_run_geojson(run_id: int, db: Session = Depends(get_db)):
    """Returns all map layers for a given run: official boundary is fetched separately via /api/quarry/geojson."""
    run = db.query(MonitoringRun).filter(MonitoringRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Monitoring run not found")
    er = run.excavation_result

    def _load(field):
        if not field:
            return None
        try:
            return json.loads(field)
        except (TypeError, json.JSONDecodeError):
            # A historic malformed geometry should not make the dashboard map
            # unusable; valid layers are still returned.
            return None

    return {
        "current_excavation": _load(er.current_excavation_geojson) if er else None,
        "previous_excavation": _load(er.previous_excavation_geojson) if er else None,
        "new_excavation": _load(er.new_excavation_geojson) if er else None,
        "unauthorized_expansion": _load(er.unauthorized_expansion_geojson) if er else None,
    }
