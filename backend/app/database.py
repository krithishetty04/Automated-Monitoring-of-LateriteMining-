"""
SQLAlchemy engine, session factory, and declarative base.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once on startup (idempotent)."""
    from app.models import quarry, monitoring_run, excavation_result, alert, user, site_update  # noqa: F401
    Base.metadata.create_all(bind=engine)
    migrate_depth_columns()


def migrate_depth_columns(bind=engine):
    # create_all does not add columns to an existing table. Apply an additive
    # migration so historical excavation results remain intact.
    additions = {
        "depth_status": "VARCHAR(32) NOT NULL DEFAULT 'UNAVAILABLE'",
        "depth_message": "TEXT",
        "mean_depth_m": "FLOAT",
        "median_depth_m": "FLOAT",
        "max_depth_m": "FLOAT",
        "min_depth_m": "FLOAT",
        "estimated_volume_m3": "FLOAT",
        "valid_elevation_samples": "INTEGER",
        "elevation_source": "VARCHAR(255)",
        "depth_method": "VARCHAR(255)",
        "before_elevation_date": "VARCHAR(20)",
        "after_elevation_date": "VARCHAR(20)",
    }
    existing = {
        column["name"]
        for column in inspect(bind).get_columns("excavation_results")
    }
    with bind.begin() as connection:
        for column, sql_type in additions.items():
            if column not in existing:
                connection.execute(text(
                    f"ALTER TABLE excavation_results ADD COLUMN {column} {sql_type}"
                ))
