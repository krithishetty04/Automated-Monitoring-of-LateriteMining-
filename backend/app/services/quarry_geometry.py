"""
Single source of truth for the official permitted quarry boundary.

IMPORTANT:
    QUARRY_COORDS represents the LEGAL boundary.

There is NO legal buffer or tolerance.

Any detected excavation outside this polygon is considered
unauthorized expansion.
"""

import math
from typing import List, Tuple, Dict, Any


# ============================================================
# OFFICIAL PERMITTED QUARRY BOUNDARY
# ============================================================

QUARRY_COORDS: List[List[float]] = [
    [74.940611, 12.992806],
    [74.940056, 12.992694],
    [74.940611, 12.994111],
    [74.941083, 12.993639],
    [74.940972, 12.993528],
    [74.940889, 12.993611],
    [74.941306, 12.992917],
    [74.940611, 12.992806],
]


_EARTH_RADIUS_M = 6378137.0


def polygon_area_hectares(
    coords: List[List[float]],
) -> float:
    """
    Approximate polygon area in hectares.

    Used only for displaying the official quarry area.
    Earth Engine is used for satellite-derived areas.
    """

    lats = [c[1] for c in coords]

    mean_lat_rad = math.radians(
        sum(lats) / len(lats)
    )

    projected: List[Tuple[float, float]] = []

    for lon, lat in coords:

        x = (
            math.radians(lon)
            * _EARTH_RADIUS_M
            * math.cos(mean_lat_rad)
        )

        y = (
            math.radians(lat)
            * _EARTH_RADIUS_M
        )

        projected.append((x, y))

    area_m2 = 0.0

    n = len(projected)

    for i in range(n):

        x1, y1 = projected[i]

        x2, y2 = projected[
            (i + 1) % n
        ]

        area_m2 += (
            x1 * y2
            - x2 * y1
        )

    area_m2 = abs(area_m2) / 2.0

    return round(
        area_m2 / 10000.0,
        4,
    )


def quarry_geojson() -> Dict[str, Any]:

    return {
        "type": "Feature",
        "properties": {
            "name": "Official Quarry Boundary"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                QUARRY_COORDS
            ],
        },
    }


def quarry_geojson_and_area():

    return (
        quarry_geojson(),
        polygon_area_hectares(
            QUARRY_COORDS
        ),
    )