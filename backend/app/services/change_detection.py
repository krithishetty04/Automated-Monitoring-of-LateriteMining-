"""
Pure decision logic: given the areas produced by the Earth Engine detection
pipeline (or a simulated scenario), decide the run's status.

Kept separate from earth_engine.py so it's easy to unit test and reuse for
the simulation/testing endpoints.
"""
from app.config import settings


def determine_status(
    is_baseline: bool,
    new_excavation_area_ha: float,
    outside_area_ha: float,
) -> str:
    """
    BASELINE  -> first-ever run, nothing to compare against
    SAFE      -> no meaningful new excavation
    PERMITTED -> new excavation exists but entirely inside the boundary
    ALERT     -> new excavation outside the boundary exceeds the threshold
    """
    if outside_area_ha >= settings.UNAUTHORIZED_AREA_THRESHOLD_HA:
        return "ALERT"

    # A baseline only means there is no earlier database observation. It must
    # never suppress detected activity outside the official legal boundary.
    if is_baseline:
        return "BASELINE"

    if new_excavation_area_ha > 0:
        return "PERMITTED"

    return "SAFE"
