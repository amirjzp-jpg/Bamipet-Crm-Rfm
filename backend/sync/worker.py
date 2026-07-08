"""
Scheduler process — runs the nightly sync (docker-compose `worker` service).

APScheduler in-process instead of OS cron so the schedule ships with the
app, is timezone-explicit, and logs into the same place as everything else.
Falls back to plain `python -m sync.worker --once` for one-off manual runs.
"""
from __future__ import annotations

import argparse
import logging
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.database import SessionLocal
from sync.job import run_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("sync.worker")


def run_once(trigger: str = "manual") -> int:
    db = SessionLocal()
    try:
        run = run_sync(db, trigger=trigger)
        logger.info("Sync run %s finished: %s", run.id, run.status)
        return 0 if run.status == "success" else 1
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bamipet RFM sync worker")
    parser.add_argument("--once", action="store_true", help="run one sync now and exit")
    args = parser.parse_args()

    if args.once:
        raise SystemExit(run_once())

    settings = get_settings()
    scheduler = BlockingScheduler(timezone="Asia/Tehran")
    scheduler.add_job(
        lambda: run_once(trigger="scheduled"),
        CronTrigger(hour=settings.SYNC_CRON_HOUR, minute=settings.SYNC_CRON_MINUTE),
        id="nightly_sync",
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        "Worker started — nightly sync at %02d:%02d Asia/Tehran (mode=%s)",
        settings.SYNC_CRON_HOUR, settings.SYNC_CRON_MINUTE, settings.NAVATEL_MODE,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
