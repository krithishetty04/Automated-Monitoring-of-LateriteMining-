"""
Orchestrates one monitoring run.

Monitoring priority:
    1. Sentinel-2 optical detection
    2. Sentinel-1 SAR fallback when Sentinel-2 has no suitable imagery

IMPORTANT:
    Sentinel-1 and Sentinel-2 are different sensors and their masks
    must never be directly compared.

    Sentinel-2:
        NDVI + BSI based excavation detection.

    Sentinel-1:
        VV/VH backscatter change detection between two compatible
        Sentinel-1 acquisitions.

Boundary:
    The official quarry polygon is the legal boundary.
    No legal buffer/tolerance is applied.

    Sentinel-1 may use an analysis area around the quarry internally,
    but the final legal classification is always performed against
    the exact official quarry polygon.
"""

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.monitoring_run import MonitoringRun
from app.models.excavation_result import ExcavationResult
from app.models.quarry import Quarry

from app.services import earth_engine
from app.services import sentinel1
from app.services.quarry_geometry import quarry_geojson_and_area
from app.services.change_detection import determine_status
from app.services.alert_service import create_alert_for_run
from app.services.depth_estimation import DepthEstimate, estimate_configured_depth


# ============================================================
# QUARRY
# ============================================================

def get_or_create_quarry(db: Session) -> Quarry:
    """
    Fetch the single Quarry row.

    If it does not exist, create it using the official quarry
    geometry.
    """

    quarry = db.query(Quarry).first()

    if quarry:
        return quarry

    geojson, area_ha = quarry_geojson_and_area()

    quarry = Quarry(
        name="Official Quarry",
        geometry_geojson=json.dumps(geojson),
        area_ha=area_ha,
    )

    db.add(quarry)
    db.commit()
    db.refresh(quarry)

    return quarry


# ============================================================
# PREVIOUS RUN
# ============================================================

def _latest_run(
    db: Session,
) -> Optional[MonitoringRun]:
    """
    Return the most recent monitoring run.
    """

    return (
        db.query(MonitoringRun)
        .order_by(
            MonitoringRun.created_at.desc()
        )
        .first()
    )


# ============================================================
# PREVIOUS SENTINEL-2 MASK
# ============================================================

def _get_previous_sentinel2_mask(
    previous_run: Optional[MonitoringRun],
):
    """
    Return the previous excavation mask ONLY when the previous
    monitoring run was Sentinel-2.

    Sentinel-1 and Sentinel-2 masks must never be compared.

    Sentinel-1 runs are identified by:
        cloud_percentage = None
    """

    if previous_run is None:
        return None

    # --------------------------------------------------------
    # Sentinel-1 runs do not have optical cloud percentage.
    # --------------------------------------------------------

    if previous_run.cloud_percentage is None:
        return None

    # --------------------------------------------------------
    # No excavation result.
    # --------------------------------------------------------

    if not previous_run.excavation_result:
        return None

    raw = (
        previous_run
        .excavation_result
        .current_excavation_geojson
    )

    if not raw:
        return None

    try:
        return json.loads(raw)

    except Exception:
        return None


# ============================================================
# MAIN MONITORING
# ============================================================

def run_monitoring(
    db: Session,
    mode: str = "real",
) -> MonitoringRun:
    """Execute one live monitoring cycle using the real Earth Engine workflow."""

    if mode != "real":
        raise ValueError("Simulation mode has been removed. Use the live monitoring workflow only.")

    # ========================================================
    # QUARRY
    # ========================================================

    quarry = get_or_create_quarry(db)

    # ========================================================
    # PREVIOUS RUN
    # ========================================================

    previous_run = _latest_run(db)

    # ========================================================
    # RESULT HOLDER
    # ========================================================

    result = None
    source = None

    # ========================================================
    # IMPORTANT:
    #
    # Only Sentinel-2 -> Sentinel-2 comparisons are allowed.
    #
    # Sentinel-1 is handled independently.
    # ====================================================

    previous_s2_mask = (
        _get_previous_sentinel2_mask(
            previous_run
        )
    )

    # ====================================================
    # FIRST: SENTINEL-2
    # ====================================================

    try:

        print(
            "[monitoring] "
            "Trying Sentinel-2 optical detection..."
        )

        result = (
            earth_engine.run_detection(
                previous_s2_mask
            )
        )

        source = "Sentinel-2"

        print(
            "[monitoring] "
            "Sentinel-2 detection successful."
        )

    # ====================================================
    # SENTINEL-1 FALLBACK
    # ====================================================

    except RuntimeError as exc:

        error_message = str(exc)

        # ------------------------------------------------
        # Only fall back when Sentinel-2 imagery is
        # unavailable.
        #
        # Do NOT hide:
        #   - authentication errors
        #   - GEE configuration errors
        #   - programming errors
        #   - geometry errors
        # ------------------------------------------------

        sentinel2_unavailable = (
            "No suitable Sentinel-2 image"
            in error_message
        )

        if not sentinel2_unavailable:
            raise

        print(
            "[monitoring] "
            "No suitable Sentinel-2 imagery found."
        )

        print(
            "[monitoring] "
            "Switching to Sentinel-1 SAR fallback..."
        )

        # ------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT pass previous Sentinel-2 mask.
        #
        # Sentinel-1 performs its own comparison between
        # two Sentinel-1 observations.
        # ------------------------------------------------

        result = sentinel1.run_detection(
            search_window_days=60
        )

        source = "Sentinel-1"

        print(
            "[monitoring] "
            "Sentinel-1 detection successful."
        )

    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if result is None:

        raise RuntimeError(
            "Monitoring pipeline returned no result."
        )

    # Depth is an optional estimate based on separately configured elevation
    # surfaces. The existing satellite detection polygon remains authoritative
    # for the footprint, and elevation failures must never stop monitoring.
    try:
        depth_estimate = estimate_configured_depth(
            result.get("new_geojson"),
            comparison_start=(
                result.get("previous_image_date")
                or (previous_run.image_date if previous_run else None)
            ),
            comparison_end=result.get("image_date"),
        )
    except Exception as exc:
        print(f"[monitoring] Optional depth estimate unavailable: {exc}")
        depth_estimate = DepthEstimate(
            status="UNAVAILABLE",
            message="Elevation depth estimation could not be completed.",
        )

    # ========================================================
    # STATUS
    # ========================================================

    is_baseline = (
        previous_run is None
    )

    status = determine_status(
        is_baseline=is_baseline,

        new_excavation_area_ha=result.get(
            "new_excavation_area_ha",
            0.0,
        ),

        outside_area_ha=result.get(
            "outside_area_ha",
            0.0,
        ),
    )

    # ========================================================
    # CREATE MONITORING RUN
    # ========================================================

    run = MonitoringRun(

        quarry_id=quarry.id,

        # ----------------------------------------------------
        # Current image
        # ----------------------------------------------------

        image_date=result[
            "image_date"
        ],

        # ----------------------------------------------------
        # Previous image
        #
        # Sentinel-2:
        #     previous S2 image/run
        #
        # Sentinel-1:
        #     previous S1 acquisition
        # ----------------------------------------------------

        previous_image_date=(
            result.get(
                "previous_image_date"
            )
            or (
                previous_run.image_date
                if previous_run
                else None
            )
        ),

        # ----------------------------------------------------
        # Cloud percentage
        #
        # Sentinel-2:
        #     actual cloud percentage
        #
        # Sentinel-1:
        #     None
        # ----------------------------------------------------

        cloud_percentage=result.get(
            "cloud_percentage"
        ),

        # ----------------------------------------------------
        # Areas
        # ----------------------------------------------------

        current_excavation_area_ha=result.get(
            "current_excavation_area_ha",
            0.0,
        ),

        previous_excavation_area_ha=result.get(
            "previous_excavation_area_ha",
            0.0,
        ),

        new_excavation_area_ha=result.get(
            "new_excavation_area_ha",
            0.0,
        ),

        inside_area_ha=result.get(
            "inside_area_ha",
            0.0,
        ),

        outside_area_ha=result.get(
            "outside_area_ha",
            0.0,
        ),

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status=status,

    )

    db.add(run)

    db.commit()

    db.refresh(run)

    # ========================================================
    # SAVE EXCAVATION RESULT
    # ========================================================

    excavation_result = ExcavationResult(

        monitoring_run_id=run.id,

        # ----------------------------------------------------
        # Current detection
        # ----------------------------------------------------

        current_excavation_geojson=(
            json.dumps(
                result["current_geojson"]
            )
            if result.get(
                "current_geojson"
            )
            else None
        ),

        # ----------------------------------------------------
        # Previous detection
        # ----------------------------------------------------

        previous_excavation_geojson=(
            json.dumps(
                result["previous_geojson"]
            )
            if result.get(
                "previous_geojson"
            )
            else None
        ),

        # ----------------------------------------------------
        # New excavation
        # ----------------------------------------------------

        new_excavation_geojson=(
            json.dumps(
                result["new_geojson"]
            )
            if result.get(
                "new_geojson"
            )
            else None
        ),

        # ----------------------------------------------------
        # Unauthorized expansion
        # ----------------------------------------------------

        unauthorized_expansion_geojson=(
            json.dumps(
                result["outside_geojson"]
            )
            if result.get(
                "outside_geojson"
            )
            else None
        ),
        **depth_estimate.as_record(),
    )

    db.add(excavation_result)

    db.commit()

    # ========================================================
    # ALERT / NOTIFICATION
    # ========================================================

    create_alert_for_run(
        db,
        run,
        status,
        result.get(
            "outside_geojson"
        ),
    )

    db.refresh(run)

    # ========================================================
    # LOG RESULT
    # ========================================================

    print(
        f"[monitoring] "
        f"Source: {source} | "
        f"Date: {result['image_date']} | "
        f"Status: {status} | "
        f"Outside area: "
        f"{result.get('outside_area_ha', 0.0)} ha"
    )

    return run
