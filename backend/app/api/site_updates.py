from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.site_update import SiteUpdate

router = APIRouter(prefix="/api/site-updates", tags=["site updates"])


class SiteUpdateCreate(BaseModel):
    area_name: Optional[str] = Field(default=None, max_length=160)
    tonnes_removed: Optional[float] = Field(default=None, ge=0)
    depth_m: Optional[float] = Field(default=None, ge=0)
    cover_status: Optional[Literal["NEEDS_COVERING", "COVERING", "COVERED", "AGRICULTURE"]] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


class SiteUpdateOut(BaseModel):
    id: int
    area_name: Optional[str]
    tonnes_removed: Optional[float]
    depth_m: Optional[float]
    cover_status: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SiteProgressOut(BaseModel):
    total_tonnes_removed: float
    has_tonnage_records: bool
    latest_depth_m: Optional[float]
    latest_depth_area: Optional[str]
    latest_depth_at: Optional[datetime]
    updates: List[SiteUpdateOut]


@router.get("", response_model=SiteProgressOut)
def get_site_progress(db: Session = Depends(get_db)):
    total = db.query(func.sum(SiteUpdate.tonnes_removed)).scalar()
    depth_update = (
        db.query(SiteUpdate)
        .filter(SiteUpdate.depth_m.isnot(None))
        .order_by(SiteUpdate.created_at.desc(), SiteUpdate.id.desc())
        .first()
    )
    updates = (
        db.query(SiteUpdate)
        .order_by(SiteUpdate.created_at.desc(), SiteUpdate.id.desc())
        .limit(30)
        .all()
    )
    return {
        "total_tonnes_removed": total or 0.0,
        "has_tonnage_records": db.query(SiteUpdate.id).filter(SiteUpdate.tonnes_removed.isnot(None)).first() is not None,
        "latest_depth_m": depth_update.depth_m if depth_update else None,
        "latest_depth_area": depth_update.area_name if depth_update else None,
        "latest_depth_at": depth_update.created_at if depth_update else None,
        "updates": updates,
    }


@router.post("", response_model=SiteUpdateOut, status_code=201)
def create_site_update(payload: SiteUpdateCreate, db: Session = Depends(get_db)):
    if payload.tonnes_removed is None and payload.depth_m is None and payload.cover_status is None and not payload.notes:
        raise HTTPException(status_code=400, detail="Enter a tonnage, depth, covering status, or note.")
    if (payload.depth_m is not None or payload.cover_status is not None) and not (payload.area_name or "").strip():
        raise HTTPException(status_code=400, detail="Enter the area or location for depth and covering updates.")

    update = SiteUpdate(
        area_name=(payload.area_name or "").strip() or None,
        tonnes_removed=payload.tonnes_removed,
        depth_m=payload.depth_m,
        cover_status=payload.cover_status,
        notes=(payload.notes or "").strip() or None,
    )
    db.add(update)
    db.commit()
    db.refresh(update)
    return update
