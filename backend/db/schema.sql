-- ============================================================
-- Reference schema for the Quarry Monitoring database.
--
-- You do NOT need to run this by hand: app/database.py's init_db()
-- creates all tables automatically from the SQLAlchemy models the first
-- time the backend starts. This file exists so you can read the schema
-- at a glance, or run it manually with psql if you ever want to set the
-- database up without starting the FastAPI app.
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255),
    hashed_password VARCHAR(255),
    is_admin        BOOLEAN DEFAULT TRUE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quarry (
    id                SERIAL PRIMARY KEY,
    name              VARCHAR(255) NOT NULL DEFAULT 'Official Quarry',
    geometry_geojson  TEXT NOT NULL,
    area_ha           FLOAT NOT NULL DEFAULT 0,
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring_runs (
    id                            SERIAL PRIMARY KEY,
    quarry_id                     INTEGER NOT NULL REFERENCES quarry(id),
    image_date                    VARCHAR(20) NOT NULL,
    previous_image_date           VARCHAR(20),
    cloud_percentage              FLOAT,
    current_excavation_area_ha    FLOAT DEFAULT 0,
    previous_excavation_area_ha   FLOAT DEFAULT 0,
    new_excavation_area_ha        FLOAT DEFAULT 0,
    inside_area_ha                FLOAT DEFAULT 0,
    outside_area_ha               FLOAT DEFAULT 0,
    status                        VARCHAR(20) NOT NULL DEFAULT 'SAFE',
    created_at                    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS excavation_results (
    id                               SERIAL PRIMARY KEY,
    monitoring_run_id                INTEGER NOT NULL REFERENCES monitoring_runs(id),
    current_excavation_geojson       TEXT,
    previous_excavation_geojson      TEXT,
    new_excavation_geojson           TEXT,
    unauthorized_expansion_geojson   TEXT,
    depth_status                     VARCHAR(32) NOT NULL DEFAULT 'UNAVAILABLE',
    depth_message                    TEXT,
    mean_depth_m                     FLOAT,
    median_depth_m                   FLOAT,
    max_depth_m                      FLOAT,
    min_depth_m                      FLOAT,
    estimated_volume_m3              FLOAT,
    valid_elevation_samples          INTEGER,
    elevation_source                 VARCHAR(255),
    depth_method                     VARCHAR(255),
    before_elevation_date            VARCHAR(20),
    after_elevation_date             VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS alerts (
    id                  SERIAL PRIMARY KEY,
    monitoring_run_id   INTEGER NOT NULL REFERENCES monitoring_runs(id),
    alert_type          VARCHAR(50) NOT NULL,
    severity            VARCHAR(20) NOT NULL DEFAULT 'HIGH',
    message             TEXT NOT NULL,
    expansion_area_ha   FLOAT DEFAULT 0,
    geometry            TEXT,
    is_read             BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_monitoring_runs_created_at ON monitoring_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON alerts(is_read);
-- Prevent duplicate alerts when a single monitoring run is retried.
CREATE UNIQUE INDEX IF NOT EXISTS uq_alerts_run_type ON alerts(monitoring_run_id, alert_type);
