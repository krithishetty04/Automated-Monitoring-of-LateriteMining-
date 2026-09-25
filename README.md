# Quarry Monitoring & Unauthorized Expansion Detection System

Weekly satellite-based monitoring of one officially permitted quarry using
Sentinel-2 imagery (NDVI + BSI) via Google Earth Engine. Detects **new**
excavation, checks whether it falls outside the permitted boundary, raises
alerts, emails an admin, and shows everything on a live map dashboard.

```
GREEN  = official permitted quarry boundary
RED    = excavation detected from satellite imagery
YELLOW = NEW excavation outside the permitted boundary  -> 🚨 ALERT
```

---

## 1. Project structure

```
quarry-monitoring/
├── backend/
│   ├── app/
│   │   ├── main.py                  FastAPI app + startup (DB init, scheduler)
│   │   ├── config.py                All settings, loaded from .env
│   │   ├── database.py              SQLAlchemy engine/session/Base
│   │   ├── models/                  quarry, user, monitoring_run, excavation_result, alert
│   │   ├── schemas/schemas.py       Pydantic request/response models
│   │   ├── api/                     monitoring.py, alerts.py, quarry.py (REST routes)
│   │   ├── services/
│   │   │   ├── quarry_geometry.py   Official polygon + pure-Python hectare calc
│   │   │   ├── earth_engine.py      Real GEE pipeline (NDVI/BSI/change detection)
│   │   │   ├── monitoring.py        Orchestrates one run (real or simulate)
│   │   │   ├── change_detection.py  Decides BASELINE/SAFE/PERMITTED/ALERT
│   │   │   ├── alert_service.py     Creates Alert rows, fires notifications
│   │   │   ├── notification_service.py  SMTP email (modular for more channels)
│   │   │   └── simulator.py         3 test scenarios, no GEE required
│   │   └── scheduler/weekly_monitor.py  APScheduler weekly job
│   ├── db/schema.sql                Reference SQL (auto-created by the app anyway)
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                        Next.js + TypeScript + Tailwind + Leaflet dashboard
│   ├── app/                         page.tsx (dashboard), layout.tsx, globals.css
│   ├── components/                  SummaryCards, MapView, AlertPanel, HistoryTable, Charts, RunControls
│   ├── services/api.ts              Typed API client
│   ├── types/index.ts
│   ├── .env.example
│   └── Dockerfile
├── gee/
│   ├── quarry_monitoring.js         Code Editor script for visual inspection
│   └── README.md
├── docker-compose.yml
└── README.md                        (this file)
```

---

## 2. What you need before you start

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or Docker, which bundles it)
- A **Google Earth Engine** account with a Cloud project that has the Earth
  Engine API enabled (free for research/non-commercial use — sign up at
  https://earthengine.google.com if you haven't). Required only for the
  **real** detection pipeline — the dashboard, database, alerts, and test
  scenarios all work without it.

---

## 3. STEP 8 — Exact commands to run everything

### Option A — Docker (simplest)

```bash
# from the quarry-monitoring/ root
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# edit backend/.env and fill in GEE_* and SMTP_* values (see Step 9 below)
# for a first smoke test you can leave GEE_* blank and only use "simulate" mode

docker compose up --build
```

- Backend: http://localhost:8000 (docs at http://localhost:8000/docs)
- Frontend dashboard: http://localhost:3000
- Postgres: localhost:5432 (user `quarry_user` / password `quarry_pass` / db `quarry_monitoring`)

To stop: `docker compose down` (add `-v` to also wipe the database volume).

### Option B — Local, no Docker

**1. Start PostgreSQL** (adjust to how you installed it locally):

```bash
# Debian/Ubuntu example
sudo service postgresql start
sudo -u postgres psql -c "CREATE USER quarry_user WITH PASSWORD 'quarry_pass';"
sudo -u postgres psql -c "CREATE DATABASE quarry_monitoring OWNER quarry_user;"
```

**2. Backend**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: DATABASE_URL, GEE_*, SMTP_* (see Step 9)

uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on startup (`init_db()` in `app/main.py`).
Leave this terminal running.

**3. Frontend** (in a new terminal)

```bash
cd frontend
npm install
cp .env.example .env
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 (already the default)

npm run dev
```

Open http://localhost:3000.

---

## 4. STEP 9 — Connect Google Earth Engine

The real detection pipeline (`app/services/earth_engine.py`) authenticates
with a **service account**, not your personal Google login — this is the
right approach for a server that runs unattended on a weekly schedule.

1. **Create/select a Google Cloud project**
   https://console.cloud.google.com/ → create a project (or reuse one).

2. **Enable the Earth Engine API** for that project
   https://console.cloud.google.com/apis/library/earthengine.googleapis.com
   → click *Enable*.

3. **Register the project for Earth Engine**
   https://code.earthengine.google.com/register → follow the prompts to
   register your Cloud project for Earth Engine access (choose the
   non-commercial/research track if that applies to you as a student).

4. **Create a service account**
   https://console.cloud.google.com/iam-admin/serviceaccounts
   → *Create Service Account* → give it any name (e.g. `quarry-monitor-bot`)
   → no special IAM roles are required for basic Earth Engine use, but
   granting it "Earth Engine Resource Viewer" is a safe default.

5. **Grant that service account Earth Engine access**
   In the Earth Engine Code Editor: https://code.earthengine.google.com/
   → gear icon → *Manage assets* → or, more directly, add the service
   account's email as a registered Earth Engine user by visiting
   https://signup.earthengine.google.com/#!/service_accounts and following
   the instructions to register it.

6. **Create and download a JSON key** for the service account
   On the service account's page → *Keys* tab → *Add Key* → *Create new
   key* → JSON → downloads a `.json` file. **Keep this file secret** — do
   not commit it.

7. **Place the key and configure `.env`**

   ```bash
   mkdir -p backend/secrets
   mv ~/Downloads/my-project-xxxxx.json backend/secrets/gee-key.json
   ```

   Edit `backend/.env`:

   ```env
   GEE_SERVICE_ACCOUNT=quarry-monitor-bot@my-project.iam.gserviceaccount.com
   GEE_PRIVATE_KEY_FILE=/absolute/path/to/quarry-monitoring/backend/secrets/gee-key.json
   GEE_PROJECT_ID=my-project
   ```

   - Running **locally (no Docker)**: use the real absolute path on your machine.
   - Running **via Docker**: `docker-compose.yml` already mounts
     `./backend/secrets` to `/run/secrets` inside the backend container, so
     set `GEE_PRIVATE_KEY_FILE=/run/secrets/gee-key.json` instead.

8. **Verify it works** — with the backend running:

   ```bash
   curl -X POST http://localhost:8000/api/monitoring/run \
     -H "Content-Type: application/json" \
     -d '{"mode": "real"}'
   ```

   If credentials are wrong, you'll get a clear `RuntimeError` message in the
   JSON response body explaining what's missing.

---

## 5. STEP 10 — Manually trigger the first monitoring run

The **first-ever run is always the baseline** (nothing to compare against
yet — `status: "BASELINE"`). Trigger it via the dashboard or the API:

**Dashboard:** open http://localhost:3000 → click **"Run Real (Earth Engine)"**
in the *Run Monitoring* bar at the top.

**API directly:**

```bash
curl -X POST http://localhost:8000/api/monitoring/run \
  -H "Content-Type: application/json" \
  -d '{"mode": "real"}'
```

Check it landed:

```bash
curl http://localhost:8000/api/monitoring/latest
```

Run it again any time (e.g. after `IMAGE_SEARCH_WINDOW_DAYS` worth of new
imagery has landed) and it will automatically diff against this baseline.
Once `ENABLE_SCHEDULER=true` (the default), this also happens automatically
every Saturday at 08:00 — configurable via `SCHEDULE_DAY_OF_WEEK`,
`SCHEDULE_HOUR`, `SCHEDULE_MINUTE` in `.env`.

---

## 6. STEP 11 — Test the three scenarios

These use `app/services/simulator.py` — structurally realistic fake
detection results that exercise the **entire pipeline** (database, alert
creation, email notification, dashboard, map, history, charts) without
touching Earth Engine. They never overwrite or interfere with real runs
beyond being additional rows in the same history (exactly like a real week
would add a row).

Easiest: use the three buttons in the **"Test Scenarios"** section of the
dashboard's control bar. Or via API:

**Case 1 — No new excavation → ✅ SAFE**

```bash
curl -X POST http://localhost:8000/api/monitoring/run \
  -H "Content-Type: application/json" \
  -d '{"mode": "simulate", "scenario": "no_change"}'
```

**Case 2 — New excavation inside the boundary → 🟢 PERMITTED ACTIVITY**

```bash
curl -X POST http://localhost:8000/api/monitoring/run \
  -H "Content-Type: application/json" \
  -d '{"mode": "simulate", "scenario": "inside"}'
```

**Case 3 — New excavation outside the boundary → 🚨 UNAUTHORIZED EXPANSION**

```bash
curl -X POST http://localhost:8000/api/monitoring/run \
  -H "Content-Type: application/json" \
  -d '{"mode": "simulate", "scenario": "outside"}'
```

This one also creates a `CRITICAL` alert and — if `SMTP_*` is configured in
`.env` — sends the email notification. Watch the *Alerts* panel and the
*Unauthorized Expansion* summary card update on the dashboard (it polls
every 45s, or just refresh).

> Tip: run scenarios in order (`no_change` → `inside` → `outside`) on a
> fresh database to see the history table build up a believable week-by-week
> story, since each simulated run's "current mask" becomes the next run's
> "previous mask" — same as real weekly monitoring.

---

## 7. Configuration reference (`backend/.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GEE_SERVICE_ACCOUNT`, `GEE_PRIVATE_KEY_FILE`, `GEE_PROJECT_ID` | Earth Engine auth (Step 9) |
| `UNAUTHORIZED_AREA_THRESHOLD_HA` | Minimum outside-boundary area (ha) that triggers an ALERT. Default `0.01` — deliberately small so minor unauthorized activity isn't missed |
| `NDVI_THRESHOLD`, `BSI_THRESHOLD` | Excavation detection rule: `NDVI < NDVI_THRESHOLD AND BSI > BSI_THRESHOLD` |
| `CLOUD_COVER_MAX` | Skip images cloudier than this (%) |
| `IMAGE_SEARCH_WINDOW_DAYS` | How far back to search for a usable image |
| `MORPHOLOGY_KERNEL_RADIUS` | Pixel-radius for noise cleanup (opening). `0` disables it |
| `ENABLE_SCHEDULER`, `SCHEDULE_DAY_OF_WEEK`, `SCHEDULE_HOUR`, `SCHEDULE_MINUTE` | Weekly automatic run schedule |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `ALERT_EMAIL`, `SMTP_USE_TLS` | SMTP connection settings. For Gmail, use an **App Password**, not your normal password |
| `ENABLE_EMAIL_NOTIFICATIONS` | Enables optional email delivery after an alert has been committed. Defaults to `false`; dashboard alerts always work independently. |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |

**Never commit `backend/.env` or `backend/secrets/*.json`** — both are in
`.gitignore` already.

---

## 8. Notes on the change-detection logic

- The system never subtracts `current_total − previous_total` (that produces
  false positives). It keeps `currentExcavationMask` and
  `previousExcavationMask` as separate raster masks, computes
  `newExcavation = current AND NOT previous`, and only *then* splits that
  into inside/outside the official polygon via geometric
  difference/intersection.
- The official boundary is used **exactly as supplied** with **no buffer**.
- Every red pixel is not illegal — only *new* excavation that falls outside
  the boundary raises the 🚨 alert; new excavation inside the boundary is
  logged as permitted activity.
- `MORPHOLOGY_KERNEL_RADIUS` defaults to a small value (1 pixel) to remove
  obvious single-pixel salt-and-pepper noise without erasing genuinely small
  new excavation patches — keep it small or set it to `0` if you'd rather
  see everything unfiltered.

## 9. Extending this project

- **Auth**: the `users` table exists but isn't wired to login yet — add
  JWT auth in `app/api/` if you need multi-user access control.
- **More notification channels**: `notification_service.py` is structured
  as a `NotificationChannel` interface — add a `WhatsAppNotificationChannel`
  or `SmsNotificationChannel` alongside `EmailNotificationChannel` and call
  it from `alert_service.py`.
- **WebSockets**: the dashboard currently polls every 45s
  (`POLL_INTERVAL_MS` in `frontend/app/page.tsx`); swapping in a WebSocket
  push is a drop-in replacement for that `setInterval`.
