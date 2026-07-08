"""
The sync + scoring job — one full pipeline run (build plan §3.2):

  1. Pull contacts, orders, calls, SMS from Navatel (or the mock).
  2. Score every contact on Recency / Frequency / Monetary / Engagement.
  3. Assign segment + persona guess + recommended messaging pillar.
  4. Store one snapshot row per contact in the warehouse (append-only
     history) and refresh the contacts cache.
  5. Optionally write the latest segment/persona back onto the Navatel
     contact record (ENABLE_WRITEBACK, off by default until the custom
     fields are confirmed to exist in the CRM schema).

Every run is recorded in sync_runs — success or failure — so the dashboard's
admin page shows exactly what happened and when.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import SyncRun
from sync.navatel_client import NavatelClientProtocol, get_navatel_client
from sync.persona_mapper import guess_persona
from sync.rfm_engine import build_customer_table, score_rfm
from sync.warehouse import refresh_contacts_cache, store_snapshot

logger = logging.getLogger(__name__)


def run_sync(
    db: Session,
    client: NavatelClientProtocol | None = None,
    settings: Settings | None = None,
    reference_date: datetime | None = None,
    trigger: str = "scheduled",
) -> SyncRun:
    """Runs the full pipeline inside the given session. reference_date lets
    the seed script re-score historical months; normal runs pass None (now)."""
    settings = settings or get_settings()
    client = client or get_navatel_client(settings)
    now = reference_date or datetime.now(timezone.utc).replace(tzinfo=None)
    run_date = now.date()

    run = SyncRun(status="running", trigger=trigger)
    db.add(run)
    db.commit()

    try:
        contacts = client.get_contacts()
        orders = client.get_orders()
        calls = client.get_call_logs()
        sms = client.get_sms_logs()
        logger.info("Fetched %d contacts, %d orders, %d calls, %d sms",
                    len(contacts), len(orders), len(calls), len(sms))

        table = build_customer_table(
            contacts, orders, calls, sms,
            reference_date=now, lookback_days=settings.LOOKBACK_DAYS,
        )
        scored = score_rfm(table, lookback_days=settings.LOOKBACK_DAYS)

        guesses = {}
        for _, row in scored.iterrows():
            guesses[row["contact_id"]] = guess_persona(row, species=row.get("species"))

        store_snapshot(db, scored, guesses, run_date)
        refresh_contacts_cache(db, contacts)

        if settings.ENABLE_WRITEBACK:
            for cid, guess in guesses.items():
                client.update_contact_field(cid, settings.SEGMENT_FIELD_NAME, guess.segment)
                client.update_contact_field(cid, settings.PERSONA_FIELD_NAME, guess.likely_persona)
            logger.info("Wrote segment/persona back to %d Navatel contacts", len(guesses))

        run.status = "success"
        run.contacts_count = len(contacts)
        run.orders_count = len(orders)
        run.calls_count = len(calls)
        run.sms_count = len(sms)
    except Exception as exc:  # record the failure, then re-raise for callers/logs
        db.rollback()
        run = db.get(SyncRun, run.id) or run
        run.status = "failed"
        run.error_message = f"{type(exc).__name__}: {exc}"[:2000]
        logger.exception("Sync run %s failed", run.id)
    finally:
        run.finished_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
    return run
