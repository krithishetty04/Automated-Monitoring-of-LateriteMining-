"""
APScheduler job that runs the real monitoring pipeline on a weekly cadence
(default: every Saturday at 08:00, configurable via .env).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.services.monitoring import run_monitoring

_scheduler: BackgroundScheduler | None = None


def _run_weekly_job():
    db = SessionLocal()
    try:
        print("[scheduler] Running weekly quarry monitoring job...")
        run = run_monitoring(db, mode="real")
        print(f"[scheduler] Monitoring run #{run.id} completed with status={run.status}")
    except Exception as exc:
        print(f"[scheduler] Weekly monitoring job failed: {exc}")
    finally:
        db.close()


def start_scheduler():
    global _scheduler
    if not settings.ENABLE_SCHEDULER:
        print("[scheduler] Scheduler disabled via ENABLE_SCHEDULER=false")
        return

    _scheduler = BackgroundScheduler()
    trigger = CronTrigger(
        day_of_week=settings.SCHEDULE_DAY_OF_WEEK,
        hour=settings.SCHEDULE_HOUR,
        minute=settings.SCHEDULE_MINUTE,
    )
    _scheduler.add_job(_run_weekly_job, trigger, id="weekly_quarry_monitoring", replace_existing=True)
    _scheduler.start()
    print(
        f"[scheduler] Weekly monitoring scheduled: every "
        f"{settings.SCHEDULE_DAY_OF_WEEK} at {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d}"
    )


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
