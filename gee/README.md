# Earth Engine script

`quarry_monitoring.js` is a **Code Editor** (code.earthengine.google.com) script
for visually inspecting a single date's NDVI / BSI / excavation detection over
the quarry. It's useful for:

- Sanity-checking the detection thresholds before changing `.env`
- Visually confirming which pixels are flagged as "excavation"
- Debugging why no image was found (check `collection.size()` output)

**It is not the production pipeline.** The real weekly pipeline — including
week-over-week comparison, new-excavation detection, and inside/outside
boundary analysis — runs server-side in the Python backend
(`backend/app/services/earth_engine.py`), because that needs to persist
state (previous week's mask) in PostgreSQL, which the Code Editor cannot do.

## How to use

1. Go to https://code.earthengine.google.com
2. Paste the contents of `quarry_monitoring.js`
3. Click "Run"
4. Check the Console for the selected image date, cloud %, and excavation area
5. Check the Map for the GREEN boundary and RED excavation overlay
