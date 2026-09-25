"""
Google Earth Engine monitoring service.

Architecture:

    Official quarry polygon
             |
             +--------------------+
             |                    |
             v                    v
       Legal boundary       100 m analysis AOI
       EXACT polygon        detection only
             |                    |
             |                    v
             |              Satellite detection
             |                    |
             +----------<---------+
                        |
                        v
              New excavation
                        |
                +-------+-------+
                |               |
             INSIDE           OUTSIDE
             legal            legal
             polygon           polygon
                |               |
             permitted       UNAUTHORIZED
                                |
                              ALERT

IMPORTANT:
    The 100 m buffer is NOT a legal buffer.

    It only tells the satellite pipeline where to search
    for possible expansion.

    The original QUARRY_COORDS polygon remains the exact
    legal boundary.
"""

import datetime as dt
import json

from typing import Optional, Dict, Any, Tuple


import ee


from app.config import settings
from app.services.quarry_geometry import QUARRY_COORDS


_initialized = False


# ============================================================
# EARTH ENGINE INITIALIZATION
# ============================================================

def initialize_ee():

    global _initialized

    if _initialized:
        return

    if (
        not settings.GEE_SERVICE_ACCOUNT
        or not settings.GEE_PRIVATE_KEY_FILE
    ):

        raise RuntimeError(
            "Earth Engine credentials are not configured. "
            "Set GEE_SERVICE_ACCOUNT, "
            "GEE_PRIVATE_KEY_FILE and GEE_PROJECT_ID "
            "in backend/.env"
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
# OFFICIAL LEGAL GEOMETRY
# ============================================================

def get_quarry_geometry():

    initialize_ee()

    return ee.Geometry.Polygon(
        [QUARRY_COORDS]
    )


# ============================================================
# ANALYSIS GEOMETRY
# ============================================================

def get_analysis_geometry(
    buffer_meters: float = 100.0,
):
    """
    Create the satellite analysis area.

    IMPORTANT:

    This buffer has NOTHING to do with legality.

    It only allows the satellite to detect excavation
    immediately outside the permitted boundary.
    """

    official_geometry = (
        get_quarry_geometry()
    )

    return official_geometry.buffer(
        buffer_meters
    )


# ============================================================
# DEBUG SENTINEL-2 IMAGES
# ============================================================

def debug_available_images(
    geometry,
    end_date: dt.date,
    search_window_days: int,
):

    start_date = (
        end_date
        - dt.timedelta(
            days=search_window_days
        )
    )

    collection = (
        ee.ImageCollection(
            "COPERNICUS/S2_SR_HARMONIZED"
        )
        .filterBounds(geometry)
        .filterDate(
            str(start_date),
            str(
                end_date
                + dt.timedelta(days=1)
            ),
        )
        .sort(
            "system:time_start",
            False,
        )
    )

    size = (
        collection
        .size()
        .getInfo()
    )

    print()
    print("=" * 70)
    print("AVAILABLE SENTINEL-2 IMAGES")
    print("=" * 70)

    print(
        f"Search period : "
        f"{start_date} -> {end_date}"
    )

    print(
        f"Total images  : {size}"
    )

    if size == 0:

        print(
            "NO SENTINEL-2 IMAGES FOUND."
        )

        print("=" * 70)

        return

    images = (
        collection
        .limit(50)
        .getInfo()
    )

    for img in images["features"]:

        props = img.get(
            "properties",
            {},
        )

        timestamp = props.get(
            "system:time_start"
        )

        cloud = props.get(
            "CLOUDY_PIXEL_PERCENTAGE"
        )

        product_id = props.get(
            "PRODUCT_ID",
            "N/A",
        )

        if timestamp:

            image_date = (
                dt.datetime
                .fromtimestamp(
                    timestamp / 1000,
                    tz=dt.timezone.utc,
                )
                .strftime(
                    "%Y-%m-%d"
                )
            )

        else:

            image_date = "unknown"

        print(
            f"Date: {image_date} | "
            f"Scene cloud: {cloud}% | "
            f"Product: {product_id}"
        )

    print("=" * 70)
    print()


# ============================================================
# SENTINEL-2 CLOUD MASK
# ============================================================

def _mask_s2_clouds(image):

    scl = image.select(
        "SCL"
    )

    bad = (
        scl.eq(3)
        .Or(scl.eq(8))
        .Or(scl.eq(9))
        .Or(scl.eq(10))
    )

    return image.updateMask(
        bad.Not()
    )


# ============================================================
# FIND SENTINEL-2 IMAGE
# ============================================================

def _find_latest_image(
    geometry,
    end_date: dt.date,
    search_window_days: int,
    cloud_max: float,
):

    start_date = (
        end_date
        - dt.timedelta(
            days=search_window_days
        )
    )

    collection = (
        ee.ImageCollection(
            "COPERNICUS/S2_SR_HARMONIZED"
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
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                cloud_max,
            )
        )
        .sort(
            "system:time_start",
            False,
        )
    )

    size = (
        collection
        .size()
        .getInfo()
    )

    print(
        f"[earth_engine] Suitable images "
        f"under {cloud_max}% cloud: {size}"
    )

    if size == 0:

        return (
            None,
            None,
            None,
        )

    image = ee.Image(
        collection.first()
    )

    props = (
        image
        .toDictionary(
            [
                "CLOUDY_PIXEL_PERCENTAGE",
                "system:time_start",
                "PRODUCT_ID",
            ]
        )
        .getInfo()
    )

    timestamp = props.get(
        "system:time_start"
    )

    if timestamp is None:

        return (
            None,
            None,
            None,
        )

    image_date = (
        dt.datetime
        .fromtimestamp(
            timestamp / 1000,
            tz=dt.timezone.utc,
        )
        .strftime(
            "%Y-%m-%d"
        )
    )

    cloud_percentage = props.get(
        "CLOUDY_PIXEL_PERCENTAGE"
    )

    print(
        f"[earth_engine] Selected image: "
        f"{image_date} | "
        f"cloud={cloud_percentage}%"
    )

    return (
        image,
        image_date,
        cloud_percentage,
    )


# ============================================================
# SENTINEL-2 EXCAVATION MASK
# ============================================================

def _excavation_mask(
    image,
    geometry,
    ndvi_threshold: float,
    bsi_threshold: float,
    kernel_radius: int,
):

    image = _mask_s2_clouds(
        image
    )

    # NDVI

    ndvi = (
        image
        .normalizedDifference(
            ["B8", "B4"]
        )
        .rename("NDVI")
    )

    # BSI

    b11 = image.select("B11")
    b4 = image.select("B4")
    b8 = image.select("B8")
    b2 = image.select("B2")

    denominator = (
        b11
        .add(b4)
        .add(b8)
        .add(b2)
    )

    bsi = (
        b11
        .add(b4)
        .subtract(
            b8.add(b2)
        )
        .divide(
            denominator
        )
        .rename("BSI")
    )

    excavation = (
        ndvi
        .lt(ndvi_threshold)
        .And(
            bsi.gt(
                bsi_threshold
            )
        )
    )

    excavation = (
        excavation
        .clip(geometry)
    )

    # Optional cleanup

    if (
        kernel_radius
        and kernel_radius > 0
    ):

        kernel = (
            ee.Kernel.circle(
                kernel_radius
            )
        )

        excavation = (
            excavation
            .focal_min(
                kernel=kernel
            )
            .focal_max(
                kernel=kernel
            )
        )

    # A 10 m Sentinel-2 pixel is 0.01 ha, the same as the alert threshold.
    # Remove isolated pixels so a transient surface response cannot by itself
    # become a reportable expansion.
    min_connected_pixels = settings.MIN_CONNECTED_PIXELS

    if min_connected_pixels > 1:

        connected_pixels = (
            excavation
            .selfMask()
            .connectedPixelCount(
                maxSize=min_connected_pixels,
                eightConnected=True,
            )
        )

        excavation = excavation.updateMask(
            connected_pixels.gte(
                min_connected_pixels
            )
        )

    return excavation.selfMask()


# ============================================================
# MASK -> GEOJSON
# ============================================================

def _mask_to_geojson(
    mask_image,
    geometry,
    scale=10,
):

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

        result = (
            vectors
            .getInfo()
        )

    except Exception as exc:

        print(
            "[earth_engine] "
            f"GeoJSON conversion failed: {exc}"
        )

        return None

    if (
        not result
        or not result.get(
            "features"
        )
    ):

        return None

    return result


# ============================================================
# MASK AREA
# ============================================================

def _mask_area_ha(
    mask_image,
    geometry,
    scale=10,
):

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
        .get(keys[0])
        .getInfo()
    )

    if value is None:

        return 0.0

    return round(
        value / 10000.0,
        4,
    )


# ============================================================
# CLASSIFY NEW EXCAVATION
# ============================================================

def _classify_new_excavation(
    new_excavation,
    official_geometry,
):

    new_geojson = (
        _mask_to_geojson(
            new_excavation,
            official_geometry.buffer(
                100
            ),
        )
    )

    if not new_geojson:

        return (
            None,
            None,
            None,
            0.0,
            0.0,
        )

    new_fc = ee.FeatureCollection(
        new_geojson
    )

    new_geom = (
        new_fc.geometry()
    )

    # ========================================================
    # IMPORTANT:
    #
    # NO BUFFER USED HERE.
    #
    # Official polygon = legal boundary.
    # ========================================================

    outside_geom = (
        new_geom.difference(
            official_geometry,
            1,
        )
    )

    inside_geom = (
        new_geom.intersection(
            official_geometry,
            1,
        )
    )

    outside_area_ha = round(
        outside_geom
        .area(1)
        .getInfo()
        / 10000.0,
        4,
    )

    inside_area_ha = round(
        inside_geom
        .area(1)
        .getInfo()
        / 10000.0,
        4,
    )

    outside_geojson = None
    inside_geojson = None

    if outside_area_ha > 0:

        try:

            outside_geojson = {
                "type": "Feature",
                "properties": {
                    "name": (
                        "Unauthorized Expansion"
                    ),
                    "classification": (
                        "OUTSIDE_PERMITTED_AREA"
                    ),
                },
                "geometry": (
                    outside_geom
                    .getInfo()
                ),
            }

        except Exception as exc:

            print(
                "[earth_engine] "
                "Outside GeoJSON error:",
                exc,
            )

    if inside_area_ha > 0:

        try:

            inside_geojson = {
                "type": "Feature",
                "properties": {
                    "name": (
                        "Permitted Excavation"
                    ),
                    "classification": (
                        "INSIDE_PERMITTED_AREA"
                    ),
                },
                "geometry": (
                    inside_geom
                    .getInfo()
                ),
            }

        except Exception as exc:

            print(
                "[earth_engine] "
                "Inside GeoJSON error:",
                exc,
            )

    return (
        new_geojson,
        inside_geojson,
        outside_geojson,
        outside_area_ha,
        inside_area_ha,
    )


# ============================================================
# MAIN SENTINEL-2 DETECTION
# ============================================================

def run_detection(
    previous_mask_geojson: Optional[
        Dict[str, Any]
    ] = None,
    reference_date: Optional[
        dt.date
    ] = None,
):

    initialize_ee()

    if reference_date is None:

        reference_date = dt.date.today()

    # ========================================================
    # TWO DIFFERENT GEOMETRIES
    # ========================================================

    official_geometry = (
        get_quarry_geometry()
    )

    analysis_geometry = (
        get_analysis_geometry(
            100
        )
    )

    print(
        "[earth_engine] Legal boundary = "
        "official quarry polygon"
    )

    print(
        "[earth_engine] No legal buffer/tolerance "
        "is being used"
    )

    print(
        "[earth_engine] Satellite analysis area = "
        "100 m around official boundary"
    )

    # ========================================================
    # DEBUG
    # ========================================================

    debug_available_images(
        geometry=analysis_geometry,
        end_date=reference_date,
        search_window_days=(
            settings.IMAGE_SEARCH_WINDOW_DAYS
        ),
    )

    # ========================================================
    # FIND IMAGE
    # ========================================================

    (
        image,
        image_date,
        cloud_percentage,
    ) = _find_latest_image(
        geometry=analysis_geometry,
        end_date=reference_date,
        search_window_days=(
            settings.IMAGE_SEARCH_WINDOW_DAYS
        ),
        cloud_max=(
            settings.CLOUD_COVER_MAX
        ),
    )

    if image is None:

        raise RuntimeError(
            "No suitable Sentinel-2 image found "
            f"in the last "
            f"{settings.IMAGE_SEARCH_WINDOW_DAYS} "
            "days with cloud cover < "
            f"{settings.CLOUD_COVER_MAX}%."
        )

    # ========================================================
    # CURRENT MASK
    #
    # IMPORTANT:
    # Detection occurs over 100 m analysis area.
    # ========================================================

    current_mask = (
        _excavation_mask(
            image=image,
            geometry=analysis_geometry,
            ndvi_threshold=(
                settings.NDVI_THRESHOLD
            ),
            bsi_threshold=(
                settings.BSI_THRESHOLD
            ),
            kernel_radius=(
                settings.MORPHOLOGY_KERNEL_RADIUS
            ),
        )
    )

    # ========================================================
    # CURRENT TOTAL AREA
    # ========================================================

    current_area_ha = (
        _mask_area_ha(
            current_mask,
            analysis_geometry,
        )
    )

    # ========================================================
    # CURRENT GEOJSON
    # ========================================================

    current_geojson = (
        _mask_to_geojson(
            current_mask,
            analysis_geometry,
        )
    )

    # ========================================================
    # DEFAULTS
    # ========================================================

    previous_area_ha = 0.0

    previous_geojson = (
        previous_mask_geojson
    )

    new_geojson = None
    inside_geojson = None
    outside_geojson = None

    new_area_ha = 0.0
    inside_area_ha = 0.0
    outside_area_ha = 0.0

    # ========================================================
    # PREVIOUS MASK
    # ========================================================

    if (
        previous_mask_geojson
        and previous_mask_geojson.get(
            "features"
        )
    ):

        previous_fc = (
            ee.FeatureCollection(
                previous_mask_geojson
            )
        )

        previous_image_mask = (
            ee.Image(0)
            .paint(
                previous_fc,
                1,
            )
            .selfMask()
            .clip(
                analysis_geometry
            )
        )

        previous_area_ha = (
            _mask_area_ha(
                previous_image_mask,
                analysis_geometry,
            )
        )

        # ====================================================
        # NEW EXCAVATION
        # ====================================================

        current_binary = (
            current_mask
            .unmask(0)
        )

        previous_binary = (
            previous_image_mask
            .unmask(0)
        )

        new_excavation = (
            current_binary
            .And(
                previous_binary.Not()
            )
            .selfMask()
            .clip(
                analysis_geometry
            )
        )

        # ====================================================
        # NEW TOTAL AREA
        # ====================================================

        new_area_ha = (
            _mask_area_ha(
                new_excavation,
                analysis_geometry,
            )
        )

        # ====================================================
        # CLASSIFY USING EXACT LEGAL BOUNDARY
        # ====================================================

        (
            new_geojson,
            inside_geojson,
            outside_geojson,
            outside_area_ha,
            inside_area_ha,
        ) = _classify_new_excavation(
            new_excavation,
            official_geometry,
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("=" * 70)
    print("SENTINEL-2 DETECTION RESULT")
    print("=" * 70)

    print(
        f"Image date: {image_date}"
    )

    print(
        f"Cloud percentage: "
        f"{cloud_percentage}%"
    )

    print(
        f"Current excavation: "
        f"{current_area_ha} ha"
    )

    print(
        f"Previous excavation: "
        f"{previous_area_ha} ha"
    )

    print(
        f"New excavation: "
        f"{new_area_ha} ha"
    )

    print(
        f"Inside permitted area: "
        f"{inside_area_ha} ha"
    )

    print(
        f"Outside permitted area: "
        f"{outside_area_ha} ha"
    )

    if outside_area_ha > 0:

        print(
            "STATUS: ALERT - "
            "UNAUTHORIZED EXPANSION"
        )

    else:

        print(
            "STATUS: SAFE"
        )

    print("=" * 70)
    print()

    return {

        "image_date":
            image_date,

        "cloud_percentage":
            cloud_percentage,

        "current_excavation_area_ha":
            current_area_ha,

        "previous_excavation_area_ha":
            previous_area_ha,

        "new_excavation_area_ha":
            new_area_ha,

        "inside_area_ha":
            inside_area_ha,

        "outside_area_ha":
            outside_area_ha,

        "current_geojson":
            current_geojson,

        "previous_geojson":
            previous_geojson,

        "new_geojson":
            new_geojson,

        "inside_geojson":
            inside_geojson,

        "outside_geojson":
            outside_geojson,
    }
