"""
Sentinel-1 SAR fallback service.

Used when Sentinel-2 does not provide a sufficiently clear image.

Sentinel-1 is radar-based and can acquire imagery through cloud cover.

Pipeline:
    1. Load official quarry polygon
    2. Create 100 m satellite analysis area around the polygon
    3. Find two compatible Sentinel-1 observations
    4. Compare VV and VH backscatter
    5. Detect significant SAR change
    6. Convert change mask to polygons
    7. Split detected change into:
         - inside official quarry boundary
         - outside official quarry boundary
    8. Calculate areas
    9. Return GeoJSON layers

IMPORTANT:
    The 100 m buffer is ONLY for satellite analysis.

    It is NOT a legal buffer.

    The official quarry polygon remains the exact legal boundary.
"""

import datetime as dt
from typing import Optional, Dict, Any, Tuple

import ee

from app.config import settings
from app.services.quarry_geometry import QUARRY_COORDS


_initialized = False


# ============================================================
# EARTH ENGINE INITIALIZATION
# ============================================================

def initialize_ee():
    """Authenticate and initialize Earth Engine once."""

    global _initialized

    if _initialized:
        return

    if (
        not settings.GEE_SERVICE_ACCOUNT
        or not settings.GEE_PRIVATE_KEY_FILE
    ):
        raise RuntimeError(
            "Earth Engine credentials are not configured. "
            "Set GEE_SERVICE_ACCOUNT, GEE_PRIVATE_KEY_FILE "
            "and GEE_PROJECT_ID in backend/.env"
        )

    credentials = ee.ServiceAccountCredentials(
        settings.GEE_SERVICE_ACCOUNT,
        settings.GEE_PRIVATE_KEY_FILE,
    )

    ee.Initialize(
        credentials,
        project=settings.GEE_PROJECT_ID or None,
    )

    _initialized = True


# ============================================================
# OFFICIAL QUARRY BOUNDARY
# ============================================================

def get_quarry_geometry():
    """
    Return the exact official quarry polygon.

    This polygon is the LEGAL boundary.
    """

    initialize_ee()

    return ee.Geometry.Polygon(
        [QUARRY_COORDS]
    )


# ============================================================
# SATELLITE ANALYSIS AREA
# ============================================================

def get_analysis_geometry(
    geometry,
    buffer_meters: float = 100.0,
):
    """
    Create the satellite analysis area.

    IMPORTANT:

    This buffer is NOT a legal tolerance.

    It only allows Sentinel-1 to detect possible excavation
    immediately outside the official quarry boundary.
    """

    return geometry.buffer(
        distance=buffer_meters,
        maxError=1,
    )


# ============================================================
# FIND SENTINEL-1 IMAGES
# ============================================================

def _find_sentinel1_images(
    geometry,
    end_date: dt.date,
    search_window_days: int,
):
    """
    Find two Sentinel-1 images suitable for comparison.

    Preference:
        - IW mode
        - GRD
        - VV
        - VH
        - 10 m resolution
        - same orbit pass
        - same relative orbit
        - different acquisition dates
    """

    start_date = (
        end_date
        - dt.timedelta(days=search_window_days)
    )

    collection = (
        ee.ImageCollection(
            "COPERNICUS/S1_GRD"
        )
        .filterBounds(geometry)
        .filterDate(
            str(start_date),
            str(
                end_date
                + dt.timedelta(days=1)
            ),
        )
        .filter(
            ee.Filter.eq(
                "instrumentMode",
                "IW",
            )
        )
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation",
                "VV",
            )
        )
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation",
                "VH",
            )
        )
        .filter(
            ee.Filter.eq(
                "resolution_meters",
                10,
            )
        )
        .sort(
            "system:time_start",
            False,
        )
    )

    size = collection.size().getInfo()

    print(
        f"[sentinel1] Available images: {size}"
    )

    if size < 2:
        return None

    image_list = collection.toList(
        collection.size()
    )

    selected = []

    for i in range(size):

        image = ee.Image(
            image_list.get(i)
        )

        props = image.toDictionary(
            [
                "system:time_start",
                "orbitProperties_pass",
                "relativeOrbitNumber_start",
            ]
        ).getInfo()

        timestamp = props.get(
            "system:time_start"
        )

        if not timestamp:
            continue

        image_date = (
            dt.datetime
            .fromtimestamp(
                timestamp / 1000.0,
                tz=dt.timezone.utc,
            )
            .strftime("%Y-%m-%d")
        )

        selected.append(
            {
                "image": image,
                "date": image_date,
                "orbit_pass": props.get(
                    "orbitProperties_pass"
                ),
                "relative_orbit": props.get(
                    "relativeOrbitNumber_start"
                ),
            }
        )

    if len(selected) < 2:
        return None

    # --------------------------------------------------------
    # Group images by acquisition geometry
    # --------------------------------------------------------

    groups = {}

    for item in selected:

        key = (
            item["orbit_pass"],
            item["relative_orbit"],
        )

        groups.setdefault(
            key,
            [],
        ).append(item)

    compatible_groups = [
        group
        for group in groups.values()
        if len(group) >= 2
    ]

    if not compatible_groups:

        print(
            "[sentinel1] No compatible orbit pair found."
        )

        return None

    # Select the group whose newest image is most recent.
    compatible = max(
        compatible_groups,
        key=lambda group: max(
            item["date"]
            for item in group
        ),
    )

    compatible = sorted(
        compatible,
        key=lambda item: item["date"],
        reverse=True,
    )

    current = compatible[0]

    previous = None

    for candidate in compatible[1:]:

        if candidate["date"] != current["date"]:

            previous = candidate

            break

    if previous is None:
        return None

    print(
        f"[sentinel1] Selected current image: "
        f"{current['date']}"
    )

    print(
        f"[sentinel1] Selected previous image: "
        f"{previous['date']}"
    )

    print(
        f"[sentinel1] Orbit pass: "
        f"{current['orbit_pass']}"
    )

    print(
        f"[sentinel1] Relative orbit: "
        f"{current['relative_orbit']}"
    )

    return current, previous


# ============================================================
# PREPARE SENTINEL-1 IMAGE
# ============================================================

def _prepare_image(
    image,
):
    """
    Select VV and VH backscatter bands.

    Sentinel-1 GRD VV/VH values in this collection are
    represented in dB.
    """

    vv = image.select(
        "VV"
    )

    vh = image.select(
        "VH"
    )

    return vv.addBands(
        vh
    )


# ============================================================
# SAR CHANGE MASK
# ============================================================

def _build_change_mask(
    current_image,
    previous_image,
    analysis_geometry,
):
    """
    Detect significant Sentinel-1 backscatter change.

    We calculate absolute change in VV and VH.

    A pixel is considered changed when either channel
    shows a significant change.

    The mask is clipped to the SATELLITE ANALYSIS AREA,
    NOT the legal boundary.

    This is essential because we need to detect possible
    excavation outside the official quarry polygon.
    """

    current = _prepare_image(
        current_image
    )

    previous = _prepare_image(
        previous_image
    )

    # --------------------------------------------------------
    # VV change
    # --------------------------------------------------------

    vv_change = (
        current
        .select("VV")
        .subtract(
            previous.select("VV")
        )
        .abs()
        .rename(
            "VV_CHANGE"
        )
    )

    # --------------------------------------------------------
    # VH change
    # --------------------------------------------------------

    vh_change = (
        current
        .select("VH")
        .subtract(
            previous.select("VH")
        )
        .abs()
        .rename(
            "VH_CHANGE"
        )
    )

    # --------------------------------------------------------
    # SAR CHANGE THRESHOLDS
    # --------------------------------------------------------

    # Initial screening values.
    #
    # These should eventually be calibrated using known
    # quarry excavation examples.

    vv_threshold = 1.5
    vh_threshold = 1.5

    vv_changed = (
        vv_change.gt(
            vv_threshold
        )
    )

    vh_changed = (
        vh_change.gt(
            vh_threshold
        )
    )

    # Either VV OR VH significant change.
    #
    # Using OR rather than AND prevents the detector from
    # missing genuine changes where only one polarization
    # responds strongly.

    change = (
        vv_changed
        .Or(vh_changed)
        .rename(
            "change"
        )
    )

    # --------------------------------------------------------
    # LIMIT TO SATELLITE ANALYSIS AREA
    # --------------------------------------------------------

    change = (
        change
        .clip(
            analysis_geometry
        )
    )

    # --------------------------------------------------------
    # MORPHOLOGICAL CLEANUP
    # --------------------------------------------------------

    kernel = ee.Kernel.circle(
        radius=1
    )

    change = (
        change
        .focal_min(
            kernel=kernel
        )
        .focal_max(
            kernel=kernel
        )
    )

    # The alert threshold equals one 10 m pixel. Require at least two
    # connected changed pixels so isolated SAR speckle or short-lived surface
    # responses do not reach the legal classification stage.
    min_connected_pixels = settings.MIN_CONNECTED_PIXELS

    if min_connected_pixels > 1:

        connected_pixels = (
            change
            .selfMask()
            .connectedPixelCount(
                maxSize=min_connected_pixels,
                eightConnected=True,
            )
        )

        change = change.updateMask(
            connected_pixels.gte(
                min_connected_pixels
            )
        )

    return change.selfMask()


# ============================================================
# MASK AREA
# ============================================================

def _mask_area_ha(
    mask_image,
    geometry,
    scale=10,
) -> float:
    """
    Calculate mask area in hectares.
    """

    area_image = (
        mask_image
        .multiply(
            ee.Image.pixelArea()
        )
    )

    stats = (
        area_image
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=scale,
            maxPixels=1e9,
            bestEffort=True,
        )
    )

    keys = (
        stats
        .keys()
        .getInfo()
    )

    if not keys:
        return 0.0

    value = (
        stats
        .get(
            keys[0]
        )
        .getInfo()
    )

    if value is None:
        return 0.0

    return round(
        value / 10000.0,
        4,
    )


# ============================================================
# MASK -> GEOJSON
# ============================================================

def _mask_to_geojson(
    mask_image,
    geometry,
    scale=10,
) -> Optional[
    Dict[str, Any]
]:
    """
    Convert binary change mask to GeoJSON.
    """

    vectors = (
        mask_image
        .reduceToVectors(
            geometry=geometry,
            scale=scale,
            geometryType="polygon",
            eightConnected=True,
            maxPixels=1e9,
            bestEffort=True,
        )
    )

    try:

        feature_collection = (
            vectors
            .getInfo()
        )

    except Exception as exc:

        print(
            "[sentinel1] "
            f"GeoJSON conversion failed: {exc}"
        )

        return None

    if (
        not feature_collection
        or not feature_collection.get(
            "features"
        )
    ):
        return None

    return feature_collection


# ============================================================
# SPLIT LEGAL / UNAUTHORIZED AREA
# ============================================================

def _split_inside_outside(
    change_geojson,
    legal_geometry,
):
    """
    Split detected change into:

        1. Inside official quarry
        2. Outside official quarry

    NO legal buffer is used.

    The analysis buffer exists only so that the satellite
    detector can see possible expansion outside the quarry.
    """

    if not change_geojson:
        return (
            None,
            None,
            0.0,
            0.0,
        )

    change_fc = (
        ee.FeatureCollection(
            change_geojson
        )
    )

    change_geometry = (
        change_fc.geometry()
    )

    # --------------------------------------------------------
    # INTERSECTION WITH LEGAL BOUNDARY
    # --------------------------------------------------------

    inside_geometry = (
        change_geometry
        .intersection(
            legal_geometry,
            1,
        )
    )

    # --------------------------------------------------------
    # DIFFERENCE FROM LEGAL BOUNDARY
    # --------------------------------------------------------

    outside_geometry = (
        change_geometry
        .difference(
            legal_geometry,
            1,
        )
    )

    # --------------------------------------------------------
    # AREAS
    # --------------------------------------------------------

    inside_area_ha = round(
        inside_geometry
        .area(1)
        .getInfo()
        / 10000.0,
        4,
    )

    outside_area_ha = round(
        outside_geometry
        .area(1)
        .getInfo()
        / 10000.0,
        4,
    )

    inside_geojson = None
    outside_geojson = None

    # --------------------------------------------------------
    # INSIDE GEOJSON
    # --------------------------------------------------------

    if inside_area_ha > 0:

        try:

            inside_geojson = {
                "type": "Feature",
                "properties": {
                    "name": (
                        "Permitted Area Change"
                    ),
                    "source": "Sentinel-1",
                },
                "geometry": (
                    inside_geometry
                    .getInfo()
                ),
            }

        except Exception as exc:

            print(
                "[sentinel1] "
                f"Inside GeoJSON error: {exc}"
            )

    # --------------------------------------------------------
    # OUTSIDE GEOJSON
    # --------------------------------------------------------

    if outside_area_ha > 0:

        try:

            outside_geojson = {
                "type": "Feature",
                "properties": {
                    "name": (
                        "Unauthorized Expansion"
                    ),
                    "source": "Sentinel-1",
                },
                "geometry": (
                    outside_geometry
                    .getInfo()
                ),
            }

        except Exception as exc:

            print(
                "[sentinel1] "
                f"Outside GeoJSON error: {exc}"
            )

    return (
        inside_geojson,
        outside_geojson,
        inside_area_ha,
        outside_area_ha,
    )


# ============================================================
# COMPLETE SENTINEL-1 DETECTION
# ============================================================

def run_detection(
    reference_date: Optional[
        dt.date
    ] = None,
    search_window_days: int = 60,
) -> Dict[str, Any]:
    """
    Run Sentinel-1 fallback detection.
    """

    initialize_ee()

    # --------------------------------------------------------
    # REFERENCE DATE
    # --------------------------------------------------------

    if reference_date is None:

        reference_date = (
            dt.date.today()
        )

    # --------------------------------------------------------
    # LEGAL BOUNDARY
    # --------------------------------------------------------

    legal_geometry = (
        get_quarry_geometry()
    )

    print(
        "[sentinel1] Legal boundary = "
        "official quarry polygon"
    )

    print(
        "[sentinel1] No legal buffer/tolerance "
        "is being used"
    )

    # --------------------------------------------------------
    # SATELLITE ANALYSIS AREA
    # --------------------------------------------------------

    analysis_geometry = (
        get_analysis_geometry(
            legal_geometry,
            buffer_meters=100,
        )
    )

    print(
        "[sentinel1] Satellite analysis area = "
        "100 m around official boundary"
    )

    # --------------------------------------------------------
    # FIND IMAGES
    # --------------------------------------------------------

    result = (
        _find_sentinel1_images(
            geometry=analysis_geometry,
            end_date=reference_date,
            search_window_days=search_window_days,
        )
    )

    if result is None:

        raise RuntimeError(
            "Could not find two compatible "
            "Sentinel-1 images in the last "
            f"{search_window_days} days."
        )

    current_info, previous_info = result

    current_image = (
        current_info["image"]
    )

    previous_image = (
        previous_info["image"]
    )

    # --------------------------------------------------------
    # BUILD CHANGE MASK
    # --------------------------------------------------------

    change_mask = (
        _build_change_mask(
            current_image=current_image,
            previous_image=previous_image,
            analysis_geometry=analysis_geometry,
        )
    )

    # --------------------------------------------------------
    # TOTAL CHANGE
    # --------------------------------------------------------

    total_change_area_ha = (
        _mask_area_ha(
            mask_image=change_mask,
            geometry=analysis_geometry,
        )
    )

    # --------------------------------------------------------
    # GEOJSON
    # --------------------------------------------------------

    change_geojson = (
        _mask_to_geojson(
            mask_image=change_mask,
            geometry=analysis_geometry,
        )
    )

    # --------------------------------------------------------
    # SPLIT LEGAL / UNAUTHORIZED
    # --------------------------------------------------------

    if change_geojson:

        (
            inside_geojson,
            outside_geojson,
            inside_area_ha,
            outside_area_ha,
        ) = _split_inside_outside(
            change_geojson=change_geojson,
            legal_geometry=legal_geometry,
        )

    else:

        inside_geojson = None
        outside_geojson = None
        inside_area_ha = 0.0
        outside_area_ha = 0.0

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = (
        "ALERT"
        if outside_area_ha > 0
        else "SAFE"
    )

    # --------------------------------------------------------
    # LOG RESULT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "SENTINEL-1 SAR DETECTION RESULT"
    )
    print("=" * 70)

    print(
        f"Current date       : "
        f"{current_info['date']}"
    )

    print(
        f"Previous date      : "
        f"{previous_info['date']}"
    )

    print(
        f"Orbit pass         : "
        f"{current_info['orbit_pass']}"
    )

    print(
        f"Relative orbit     : "
        f"{current_info['relative_orbit']}"
    )

    print(
        f"Total SAR change   : "
        f"{total_change_area_ha} ha"
    )

    print(
        f"Inside permitted   : "
        f"{inside_area_ha} ha"
    )

    print(
        f"Outside permitted  : "
        f"{outside_area_ha} ha"
    )

    print(
        f"Status             : "
        f"{status}"
    )

    print(
        "Legal boundary     : "
        "Official Quarry Polygon"
    )

    print(
        "Satellite buffer   : "
        "100 m analysis area ONLY"
    )

    print(
        "Legal buffer       : "
        "NONE"
    )

    print("=" * 70)
    print()

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "source": "Sentinel-1",

        "image_date": (
            current_info["date"]
        ),

        "previous_image_date": (
            previous_info["date"]
        ),

        "cloud_percentage": None,

        "current_excavation_area_ha": (
            total_change_area_ha
        ),

        "previous_excavation_area_ha": 0.0,

        "new_excavation_area_ha": (
            total_change_area_ha
        ),

        "inside_area_ha": (
            inside_area_ha
        ),

        "outside_area_ha": (
            outside_area_ha
        ),

        "current_geojson": (
            change_geojson
        ),

        "previous_geojson": None,

        "new_geojson": (
            change_geojson
        ),

        "inside_geojson": (
            inside_geojson
        ),

        "outside_geojson": (
            outside_geojson
        ),

        "orbit_pass": (
            current_info["orbit_pass"]
        ),

        "relative_orbit": (
            current_info["relative_orbit"]
        ),
    }
