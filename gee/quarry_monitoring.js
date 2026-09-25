// ============================================================
// Quarry Monitoring - Google Earth Engine Code Editor script
// Use this in https://code.earthengine.google.com to visually
// inspect NDVI/BSI/excavation detection for a chosen date, and
// to sanity-check what the Python backend (app/services/earth_engine.py)
// computes. This is a helper/inspection script, not the production
// pipeline (that runs server-side via the Python backend).
// ============================================================

var quarry = ee.Geometry.Polygon([
  [
    [74.940611, 12.992806],
    [74.940056, 12.992694],
    [74.940611, 12.994111],
    [74.941083, 12.993639],
    [74.940972, 12.993528],
    [74.940889, 12.993611],
    [74.941306, 12.992917],
    [74.940611, 12.992806]
  ]
]);

// ---------- Config (mirror of backend/.env thresholds) ----------
var NDVI_THRESHOLD = 0.2;
var BSI_THRESHOLD = 0.1;
var CLOUD_MAX = 20;
var END_DATE = ee.Date(Date.now());          // "today"
var START_DATE = END_DATE.advance(-30, 'day'); // 30-day search window

// ---------- Cloud mask using SCL band ----------
function maskS2Clouds(image) {
  var scl = image.select('SCL');
  var bad = scl.eq(3).or(scl.eq(8)).or(scl.eq(9)).or(scl.eq(10));
  return image.updateMask(bad.not());
}

// ---------- Get the latest suitable image ----------
var collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(quarry)
  .filterDate(START_DATE, END_DATE.advance(1, 'day'))
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_MAX))
  .sort('system:time_start', false);

print('Number of suitable images in window:', collection.size());

var image = ee.Image(collection.first());
image = maskS2Clouds(image);

print('Selected image date:', image.date());
print('Cloud %:', image.get('CLOUDY_PIXEL_PERCENTAGE'));

// ---------- NDVI ----------
var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');

// ---------- BSI ----------
var bsi = image.select('B11').add(image.select('B4'))
  .subtract(image.select('B8').add(image.select('B2')))
  .divide(
    image.select('B11').add(image.select('B4'))
      .add(image.select('B8').add(image.select('B2')))
  )
  .rename('BSI');

// ---------- Excavation mask ----------
var excavation = ndvi.lt(NDVI_THRESHOLD).and(bsi.gt(BSI_THRESHOLD)).rename('excavation');
excavation = excavation.clip(quarry).selfMask();

// ---------- Area ----------
var areaImage = excavation.multiply(ee.Image.pixelArea());
var areaStats = areaImage.reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: quarry,
  scale: 10,
  maxPixels: 1e9,
  bestEffort: true
});
print('Excavation area (ha):', ee.Number(areaStats.get('excavation')).divide(10000));

// ---------- Visualization ----------
Map.centerObject(quarry, 17);
Map.addLayer(quarry, {color: 'green'}, 'Official Boundary (GREEN)');
Map.addLayer(excavation, {palette: ['red']}, 'Detected Excavation (RED)');
Map.addLayer(image, {bands: ['B4', 'B3', 'B2'], min: 0, max: 3000}, 'True Color', false);
Map.addLayer(ndvi, {min: -1, max: 1, palette: ['red', 'white', 'green']}, 'NDVI', false);
Map.addLayer(bsi, {min: -1, max: 1, palette: ['blue', 'white', 'brown']}, 'BSI', false);

// ============================================================
// NOTE ON CHANGE DETECTION IN THIS SCRIPT:
// The Code Editor is stateless between runs, so week-over-week
// comparison (previous vs current mask, new-excavation-outside-boundary)
// is implemented in the Python backend (app/services/earth_engine.py),
// which persists each week's mask in PostgreSQL and diffs it against
// this week's mask. This script is for visual inspection of a single
// date only.
// ============================================================
