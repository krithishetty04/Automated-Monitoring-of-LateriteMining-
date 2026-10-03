"""Optional elevation-derived depth estimates for existing detected polygons.

Sentinel imagery is used only to provide the excavation footprint. Depth is
calculated only when two real, configured elevation rasters are available.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Optional

import numpy as np

from app.config import settings


@dataclass(frozen=True)
class DepthEstimate:
    status: str
    mean_depth_m: Optional[float] = None
    median_depth_m: Optional[float] = None
    max_depth_m: Optional[float] = None
    min_depth_m: Optional[float] = None
    estimated_volume_m3: Optional[float] = None
    valid_elevation_samples: int = 0
    elevation_source: Optional[str] = None
    depth_method: Optional[str] = None
    before_elevation_date: Optional[str] = None
    after_elevation_date: Optional[str] = None
    message: Optional[str] = None

    def as_record(self) -> dict[str, Any]:
        return {
            "depth_status": self.status,
            "mean_depth_m": self.mean_depth_m,
            "median_depth_m": self.median_depth_m,
            "max_depth_m": self.max_depth_m,
            "min_depth_m": self.min_depth_m,
            "estimated_volume_m3": self.estimated_volume_m3,
            "valid_elevation_samples": self.valid_elevation_samples,
            "elevation_source": self.elevation_source,
            "depth_method": self.depth_method,
            "before_elevation_date": self.before_elevation_date,
            "after_elevation_date": self.after_elevation_date,
            "depth_message": self.message,
        }


METHOD = (
    "Positive elevation difference: max(0, before - after); "
    "volume=sum(depth x valid pixel area)"
)
VERTICAL_UNIT_TO_METRES = {
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "metre": 1.0,
    "metres": 1.0,
    "ft": 0.3048,
    "foot": 0.3048,
    "feet": 0.3048,
}


def unavailable(message: str) -> DepthEstimate:
    return DepthEstimate(status="UNAVAILABLE", message=message)


def insufficient(message: str, *, valid_samples: int = 0) -> DepthEstimate:
    return DepthEstimate(
        status="INSUFFICIENT_DATA",
        valid_elevation_samples=valid_samples,
        message=message,
    )


def calculate_depth_metrics(
    before: Iterable[Any],
    after: Iterable[Any],
    pixel_area_m2: float,
    *,
    valid_mask: Optional[Iterable[Any]] = None,
    minimum_valid_samples: int = 1,
) -> DepthEstimate:
    """Calculate positive lowering metrics from aligned elevation samples."""
    before_values = np.ma.asarray(before, dtype=float)
    after_values = np.ma.asarray(after, dtype=float)
    if before_values.shape != after_values.shape:
        return insufficient("Before and after elevations are not aligned.")
    if not np.isfinite(pixel_area_m2) or pixel_area_m2 <= 0:
        return insufficient("Elevation pixels do not have a valid ground area.")

    before_data = np.asarray(before_values.filled(np.nan), dtype=float)
    after_data = np.asarray(after_values.filled(np.nan), dtype=float)
    valid = np.isfinite(before_data) & np.isfinite(after_data)
    if valid_mask is not None:
        supplied_mask = np.asarray(valid_mask, dtype=bool)
        if supplied_mask.shape != valid.shape:
            return insufficient("The excavation mask does not match the elevation grid.")
        valid &= supplied_mask

    count = int(valid.sum())
    if count == 0:
        return insufficient("No overlapping valid elevation pixels inside the detected excavation polygon.")
    if count < minimum_valid_samples:
        return insufficient(
            f"Only {count} valid elevation sample(s); {minimum_valid_samples} are required.",
            valid_samples=count,
        )

    depths = np.maximum(0.0, before_data[valid] - after_data[valid])
    return DepthEstimate(
        status="ESTIMATE",
        mean_depth_m=float(np.mean(depths)),
        median_depth_m=float(np.median(depths)),
        max_depth_m=float(np.max(depths)),
        min_depth_m=float(np.min(depths)),
        estimated_volume_m3=float(np.sum(depths) * pixel_area_m2),
        valid_elevation_samples=count,
        elevation_source=settings.ELEVATION_DATA_SOURCE or "Configured GeoTIFF elevation surfaces",
        depth_method=METHOD,
        before_elevation_date=settings.ELEVATION_BEFORE_DATE or None,
        after_elevation_date=settings.ELEVATION_AFTER_DATE or None,
        message=(
            "Elevation-based estimate; source resolution and field validation "
            "determine how representative it is of quarry depth."
        ),
    )


def _extract_geometries(geojson: Any) -> list[dict[str, Any]]:
    if not isinstance(geojson, dict):
        return []
    kind = geojson.get("type")
    if kind == "Feature":
        geometry = geojson.get("geometry")
        return [geometry] if isinstance(geometry, dict) else []
    if kind == "FeatureCollection":
        return [
            feature["geometry"]
            for feature in geojson.get("features", [])
            if isinstance(feature, dict) and isinstance(feature.get("geometry"), dict)
        ]
    if kind in {"Polygon", "MultiPolygon"}:
        return [geojson]
    return []


def _valid_polygonal_geometry(geometry: dict[str, Any]) -> bool:
    """Basic finite-coordinate and non-zero-ring-area guard before raster masking."""
    if geometry.get("type") == "Polygon":
        polygons = [geometry.get("coordinates")]
    elif geometry.get("type") == "MultiPolygon":
        polygons = geometry.get("coordinates")
    else:
        return False

    if not isinstance(polygons, list) or not polygons:
        return False
    has_area = False
    try:
        for polygon in polygons:
            if not isinstance(polygon, list) or not polygon:
                return False
            ring = polygon[0]
            if not isinstance(ring, list) or len(ring) < 4:
                return False
            points = [(float(point[0]), float(point[1])) for point in ring]
            if not all(np.isfinite(point).all() for point in points):
                return False
            area2 = abs(sum(
                x1 * y2 - x2 * y1
                for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
            ))
            has_area |= area2 > 0
    except (TypeError, ValueError, IndexError):
        return False
    return has_area


def estimate_configured_depth(
    geojson: Any,
    comparison_start: Optional[str] = None,
    comparison_end: Optional[str] = None,
) -> DepthEstimate:
    """Clip and compare configured before/after GeoTIFF surfaces to a detected polygon.

    The after surface is warped to the before surface's CRS and grid using
    bilinear resampling. Elevation rasters must use a projected metre CRS so
    their pixel area can support a cubic-metre volume estimate.
    """
    before_path = settings.ELEVATION_BEFORE_RASTER
    after_path = settings.ELEVATION_AFTER_RASTER
    if not before_path or not after_path:
        return unavailable(
            "Before and after elevation rasters are not configured. "
            "Sentinel imagery supplies the detected area, not depth."
        )
    if not Path(before_path).is_file() or not Path(after_path).is_file():
        return unavailable("A configured before or after elevation raster file is missing.")
    vertical_units = settings.ELEVATION_VERTICAL_UNITS.strip().lower()
    vertical_unit_factor = VERTICAL_UNIT_TO_METRES.get(vertical_units)
    if vertical_unit_factor is None:
        return unavailable("Set ELEVATION_VERTICAL_UNITS to m or ft after confirming the elevation raster units.")
    if not comparison_start or not comparison_end:
        return unavailable("A previous and current imagery date are required to match this elevation pair to the detected change interval.")
    try:
        before_date = date.fromisoformat(settings.ELEVATION_BEFORE_DATE)
        after_date = date.fromisoformat(settings.ELEVATION_AFTER_DATE)
        start_date = date.fromisoformat(comparison_start)
        end_date = date.fromisoformat(comparison_end)
    except (TypeError, ValueError):
        return unavailable("Configure valid ISO dates for the before/after elevation surfaces and monitoring interval.")
    if not (before_date <= start_date < after_date <= end_date):
        return unavailable(
            "The configured elevation dates do not bracket the latest detected-change interval; "
            "the surfaces were not reused for this run."
        )

    geometries = _extract_geometries(geojson)
    if not geometries:
        return insufficient("This monitoring run has no detected excavation polygon to measure.")
    if not all(_valid_polygonal_geometry(geometry) for geometry in geometries):
        return insufficient("The detected excavation geometry is invalid or has zero area.")

    try:
        import rasterio
        from rasterio.features import geometry_mask, geometry_window
        from rasterio.windows import Window
        from rasterio.warp import Resampling, reproject, transform_geom
        from shapely.geometry import shape

        polygon_shapes = [shape(geometry) for geometry in geometries]
        if any(
            polygon.is_empty or not polygon.is_valid or polygon.area <= 0
            for polygon in polygon_shapes
        ):
            return insufficient("The detected excavation geometry is invalid or has zero area.")
        geometries = [polygon.__geo_interface__ for polygon in polygon_shapes]

        with rasterio.open(before_path) as before_ds, rasterio.open(after_path) as after_ds:
            if before_ds.crs is None or after_ds.crs is None:
                return insufficient("Both elevation rasters must declare their coordinate reference system.")
            if not before_ds.crs.is_projected or before_ds.crs.linear_units.lower() not in {"metre", "meter"}:
                return insufficient("The reference elevation raster must use a projected coordinate system in metres.")
            metadata_units = [
                (dataset.units[0] or "").strip().lower() if dataset.units else ""
                for dataset in (before_ds, after_ds)
            ]
            if any(
                unit and VERTICAL_UNIT_TO_METRES.get(unit) != vertical_unit_factor
                for unit in metadata_units
            ):
                return insufficient("Configured vertical units conflict with elevation raster metadata.")
            if before_ds.width == 0 or before_ds.height == 0 or after_ds.width == 0 or after_ds.height == 0:
                return insufficient("An elevation raster has no pixels.")

            raster_geometries = [
                transform_geom("EPSG:4326", before_ds.crs, geometry)
                for geometry in geometries
            ]
            window = geometry_window(before_ds, raster_geometries).intersection(
                Window(0, 0, before_ds.width, before_ds.height)
            ).round_offsets().round_lengths()
            before = before_ds.read(1, window=window, masked=True).astype("float64").filled(np.nan)
            aligned_after = np.full(before.shape, np.nan, dtype="float64")
            reference_transform = before_ds.window_transform(window)
            reproject(
                source=rasterio.band(after_ds, 1),
                destination=aligned_after,
                src_transform=after_ds.transform,
                src_crs=after_ds.crs,
                src_nodata=after_ds.nodata,
                dst_transform=reference_transform,
                dst_crs=before_ds.crs,
                dst_nodata=np.nan,
                resampling=Resampling.bilinear,
                init_dest_nodata=True,
            )
            before *= vertical_unit_factor
            aligned_after *= vertical_unit_factor

            inside_polygon = geometry_mask(
                raster_geometries,
                out_shape=before.shape,
                transform=reference_transform,
                all_touched=False,
                invert=True,
            )
            pixel_area_m2 = abs(
                before_ds.transform.a * before_ds.transform.e
                - before_ds.transform.b * before_ds.transform.d
            )
            return calculate_depth_metrics(
                before,
                aligned_after,
                pixel_area_m2,
                valid_mask=inside_polygon,
                minimum_valid_samples=settings.DEPTH_MIN_VALID_SAMPLES,
            )
    except ImportError:
        return unavailable("Elevation processing dependencies are not installed; install rasterio and shapely.")
    except Exception as exc:
        return insufficient(f"Elevation rasters could not be aligned or clipped: {exc}")
