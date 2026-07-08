"""Seeds the warehouse with demo history: re-scores the mock Navatel dataset
at seven monthly reference dates (6 months ago → today), so the dashboard's
trend and migration views have real movement to show on first open.

    python -m scripts.seed_demo

Safe to re-run (snapshot writes are idempotent per run_date). Only intended
for NAVATEL_MODE=mock; refuses to run against live mode so demo rows can
never mix into real data.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.database import SessionLocal
from sync.job import run_sync
from sync.mock_navatel import MockNavatelClient


def main() -> int:
    settings = get_settings()
    if settings.NAVATEL_MODE != "mock":
        print("Refusing to seed demo data while NAVATEL_MODE != 'mock'.", file=sys.stderr)
        return 1

    client = MockNavatelClient()
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    reference_dates = [today - timedelta(days=30 * n) for n in range(6, 0, -1)] + [today]

    db = SessionLocal()
    try:
        for ref in reference_dates:
            run = run_sync(db, client=client, settings=settings, reference_date=ref, trigger="seed")
            print(f"  {ref.date()}: {run.status} "
                  f"({run.contacts_count} contacts, {run.orders_count} orders)")
            if run.status != "success":
                print(f"Seed failed at {ref.date()}: {run.error_message}", file=sys.stderr)
                return 1
        print("Demo warehouse seeded — 7 monthly snapshots.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
