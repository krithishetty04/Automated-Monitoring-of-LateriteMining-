from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.schemas.schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/unread", response_model=List[AlertOut])
def list_unread_alerts(db: Session = Depends(get_db)):
    return (
        db.query(Alert)
        .filter(Alert.is_read == False)  # noqa: E712
        .order_by(Alert.created_at.desc())
        .all()
    )


@router.post("/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
