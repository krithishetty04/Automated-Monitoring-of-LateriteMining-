
import json
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.monitoring_run import MonitoringRun
from app.config import settings
from app.services.notification_service import send_unauthorized_expansion_email


def create_alert_for_run(
    db: Session,
    run: MonitoringRun,
    status: str,
    outside_geojson: Optional[Dict[str, Any]],
) -> Optional[Alert]:
    """
    Create and store an Alert for the monitoring run.

    Alerts are stored in the database so the dashboard can display them.

    Alert persistence is independent from optional email notifications. The
    dashboard always reads the committed Alert record from the API.
    """

    # ============================================================
    # UNAUTHORIZED EXPANSION
    # ============================================================

    if status == "ALERT":

        # A retry or accidental second invocation for the same run must not
        # create a second dashboard alert. Different monitoring runs remain
        # distinct alerts, even when they use the same image date.
        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.monitoring_run_id == run.id,
                Alert.alert_type == "UNAUTHORIZED_EXPANSION",
            )
            .first()
        )
        if existing_alert:
            return existing_alert

        alert = Alert(
            monitoring_run_id=run.id,

            alert_type="UNAUTHORIZED_EXPANSION",

            severity="CRITICAL",

            message=(
                f"Potential unauthorized quarry expansion detected on "
                f"{run.image_date}: "
                f"{run.outside_area_ha} ha of new excavation "
                f"found outside the permitted boundary."
            ),

            expansion_area_ha=run.outside_area_ha,

            geometry=(
                json.dumps(outside_geojson)
                if outside_geojson
                else None
            ),

            is_read=False,
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Email must never control alert creation. It is attempted only after
        # the alert is safely committed, and failures stay non-fatal.
        if settings.ENABLE_EMAIL_NOTIFICATIONS:
            send_unauthorized_expansion_email(
                run.image_date,
                run.outside_area_ha,
            )

        return alert

    # ============================================================
    # PERMITTED ACTIVITY
    # ============================================================

    if status == "PERMITTED":

        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.monitoring_run_id == run.id,
                Alert.alert_type == "PERMITTED_ACTIVITY",
            )
            .first()
        )
        if existing_alert:
            return existing_alert

        alert = Alert(
            monitoring_run_id=run.id,

            alert_type="PERMITTED_ACTIVITY",

            severity="LOW",

            message=(
                f"New excavation of "
                f"{run.new_excavation_area_ha} ha detected on "
                f"{run.image_date}, fully within the permitted "
                f"boundary."
            ),

            expansion_area_ha=0.0,

            geometry=None,

            is_read=False,
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        return alert

    # ============================================================
    # SAFE / OTHER
    # ============================================================

    return None
