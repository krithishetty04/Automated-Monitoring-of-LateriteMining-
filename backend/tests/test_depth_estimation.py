import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from app.schemas.schemas import ExcavationResultOut
from app.services.depth_estimation import (
    calculate_depth_metrics,
    estimate_configured_depth,
    _valid_polygonal_geometry,
)
from app.config import settings
from app.database import migrate_depth_columns
from sqlalchemy import create_engine, text


class DepthMetricTests(unittest.TestCase):
    def test_same_elevation_is_zero_depth(self):
        result = calculate_depth_metrics([100, 101, 102], [100, 101, 102], 2)
        self.assertEqual(result.status, "ESTIMATE")
        self.assertEqual(result.mean_depth_m, 0)
        self.assertEqual(result.max_depth_m, 0)
        self.assertEqual(result.estimated_volume_m3, 0)

    def test_excavation_statistics(self):
        result = calculate_depth_metrics([100, 100, 100], [98, 97, 99], 1)
        self.assertEqual(result.mean_depth_m, 2)
        self.assertEqual(result.median_depth_m, 2)
        self.assertEqual(result.max_depth_m, 3)
        self.assertEqual(result.min_depth_m, 1)
        self.assertEqual(result.valid_elevation_samples, 3)

    def test_negative_differences_are_clamped_to_zero(self):
        result = calculate_depth_metrics([100, 100], [101, 99], 1)
        self.assertEqual(result.mean_depth_m, 0.5)
        self.assertEqual(result.max_depth_m, 1)
        self.assertEqual(result.min_depth_m, 0)

    def test_null_nan_and_masked_samples_are_ignored(self):
        before = np.ma.array([100, 100, 100, 100], mask=[False, True, False, False])
        after = [98, 98, np.nan, 99]
        result = calculate_depth_metrics(before, after, 2)
        self.assertEqual(result.valid_elevation_samples, 2)
        self.assertEqual(result.mean_depth_m, 1.5)
        self.assertEqual(result.estimated_volume_m3, 6)

    def test_no_overlapping_valid_pixels_is_insufficient(self):
        result = calculate_depth_metrics([100, 100], [99, 99], 1, valid_mask=[False, False])
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIsNone(result.mean_depth_m)
        self.assertEqual(result.valid_elevation_samples, 0)

    def test_volume_uses_pixel_area(self):
        result = calculate_depth_metrics([100, 100], [99, 98], 25)
        self.assertEqual(result.estimated_volume_m3, 75)

    def test_misaligned_arrays_are_rejected(self):
        result = calculate_depth_metrics([100, 100], [99], 1)
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIsNone(result.estimated_volume_m3)

    def test_invalid_zero_area_polygon_is_detected(self):
        geometry = {
            "type": "Polygon",
            "coordinates": [[[74, 13], [74, 13], [74, 13], [74, 13]]],
        }
        self.assertFalse(_valid_polygonal_geometry(geometry))

    def test_missing_elevation_configuration_is_unavailable(self):
        with patch.object(settings, "ELEVATION_BEFORE_RASTER", ""), patch.object(settings, "ELEVATION_AFTER_RASTER", ""):
            result = estimate_configured_depth({"type": "FeatureCollection", "features": []})
        self.assertEqual(result.status, "UNAVAILABLE")
        self.assertIsNone(result.mean_depth_m)

    def test_elevation_pair_must_match_the_monitoring_change_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory) / "before.tif"
            after = Path(directory) / "after.tif"
            before.touch()
            after.touch()
            polygon = {"type": "Polygon", "coordinates": [[[74, 13], [74.1, 13], [74.1, 13.1], [74, 13.1], [74, 13]]]}
            with patch.object(settings, "ELEVATION_BEFORE_RASTER", str(before)), patch.object(settings, "ELEVATION_AFTER_RASTER", str(after)), patch.object(settings, "ELEVATION_VERTICAL_UNITS", "m"), patch.object(settings, "ELEVATION_BEFORE_DATE", "2026-01-01"), patch.object(settings, "ELEVATION_AFTER_DATE", "2026-02-01"):
                result = estimate_configured_depth(polygon, "2026-03-01", "2026-04-01")
        self.assertEqual(result.status, "UNAVAILABLE")
        self.assertIn("not reused", result.message)

    def test_historical_result_without_depth_fields_remains_valid(self):
        historical = ExcavationResultOut.model_validate({
            "id": 7,
            "current_excavation_geojson": None,
            "previous_excavation_geojson": None,
            "new_excavation_geojson": None,
            "unauthorized_expansion_geojson": None,
        })
        self.assertIsNone(historical.mean_depth_m)
        self.assertIsNone(historical.depth_status)

    def test_additive_database_migration_preserves_historical_rows(self):
        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE excavation_results (id INTEGER PRIMARY KEY, monitoring_run_id INTEGER, current_excavation_geojson TEXT, previous_excavation_geojson TEXT, new_excavation_geojson TEXT, unauthorized_expansion_geojson TEXT)"
                ))
                connection.execute(text(
                    "INSERT INTO excavation_results (id, monitoring_run_id) VALUES (41, 9)"
                ))
            migrate_depth_columns(engine)
            migrate_depth_columns(engine)
            with engine.connect() as connection:
                row = connection.execute(text(
                    "SELECT id, depth_status, mean_depth_m FROM excavation_results WHERE id = 41"
                )).one()
            self.assertEqual(row.id, 41)
            self.assertEqual(row.depth_status, "UNAVAILABLE")
            self.assertIsNone(row.mean_depth_m)
        finally:
            engine.dispose()

    def test_zero_area_geometry_returns_insufficient_with_configured_files(self):
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory) / "before.tif"
            after = Path(directory) / "after.tif"
            before.touch()
            after.touch()
            geometry = {"type": "Polygon", "coordinates": [[[74, 13], [74, 13], [74, 13], [74, 13]]]}
            with patch.object(settings, "ELEVATION_BEFORE_RASTER", str(before)), patch.object(settings, "ELEVATION_AFTER_RASTER", str(after)), patch.object(settings, "ELEVATION_VERTICAL_UNITS", "m"), patch.object(settings, "ELEVATION_BEFORE_DATE", "2025-01-01"), patch.object(settings, "ELEVATION_AFTER_DATE", "2025-01-15"):
                result = estimate_configured_depth(geometry, "2025-01-01", "2025-02-01")
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIsNone(result.mean_depth_m)


try:
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.warp import transform
except ImportError:
    rasterio = None


@unittest.skipUnless(rasterio is not None, "rasterio is not installed in this environment")
class RasterAlignmentTests(unittest.TestCase):
    def test_different_raster_resolutions_are_aligned_before_calculation(self):
        from rasterio.crs import CRS
        from shapely.geometry import Polygon, mapping
        crs = CRS.from_epsg(32643)
        bounds = [(500000, 1440000), (500030, 1440000), (500030, 1439970), (500000, 1439970), (500000, 1440000)]
        lon, lat = transform(crs, CRS.from_epsg(4326), [point[0] for point in bounds], [point[1] for point in bounds])
        polygon = Polygon(zip(lon, lat))
        geojson = mapping(polygon)

        with tempfile.TemporaryDirectory() as directory:
            before_path = Path(directory) / "before.tif"
            after_path = Path(directory) / "after.tif"
            with rasterio.open(before_path, "w", driver="GTiff", height=3, width=3, count=1, dtype="float32", crs=crs, transform=from_origin(500000, 1440000, 10, 10), nodata=-9999) as dst:
                dst.write(np.full((3, 3), 100, dtype="float32"), 1)
            with rasterio.open(after_path, "w", driver="GTiff", height=6, width=6, count=1, dtype="float32", crs=crs, transform=from_origin(500000, 1440000, 5, 5), nodata=-9999) as dst:
                dst.write(np.full((6, 6), 98, dtype="float32"), 1)

            with patch.object(settings, "ELEVATION_BEFORE_RASTER", str(before_path)), patch.object(settings, "ELEVATION_AFTER_RASTER", str(after_path)), patch.object(settings, "ELEVATION_VERTICAL_UNITS", "m"), patch.object(settings, "ELEVATION_BEFORE_DATE", "2025-01-01"), patch.object(settings, "ELEVATION_AFTER_DATE", "2025-01-15"), patch.object(settings, "DEPTH_MIN_VALID_SAMPLES", 3):
                result = estimate_configured_depth(geojson, "2025-01-01", "2025-02-01")

        self.assertEqual(result.status, "ESTIMATE")
        self.assertAlmostEqual(result.mean_depth_m, 2, places=5)
        self.assertEqual(result.valid_elevation_samples, 9)
        self.assertAlmostEqual(result.estimated_volume_m3, 1800, places=4)


if __name__ == "__main__":
    unittest.main()
