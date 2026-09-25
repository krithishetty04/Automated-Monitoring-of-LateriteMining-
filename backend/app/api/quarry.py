import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.quarry import Quarry
from app.schemas.schemas import QuarryOut
from app.services.monitoring import get_or_create_quarry

router = APIRouter(prefix="/api/quarry", tags=["quarry"])


@router.get("", response_model=QuarryOut)
def get_quarry(db: Session = Depends(get_db)):
    quarry = get_or_create_quarry(db)
    return quarry


@router.get("/geojson")
def get_quarry_geojson(db: Session = Depends(get_db)):
    quarry = get_or_create_quarry(db)
    return json.loads(quarry.geometry_geojson)
