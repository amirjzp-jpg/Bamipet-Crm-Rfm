"""Persists a scored RFM+E run into the warehouse — the piece between
"compute scores" and "dashboard reads Postgres."

Snapshots are append-only per (contact_id, run_date): re-running the same
day's sync REPLACES that day's rows (idempotent — a retried nightly job
doesn't duplicate), but never touches any other date's history.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import ContactCache, RfmSnapshot
from sync.persona_mapper import PersonaGuess


def _none_if_nan(value):
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return None
    return value


def store_snapshot(
    db: Session,
    scored: pd.DataFrame,
    guesses: dict[str, PersonaGuess],
    run_date: date,
) -> int:
    """Writes one snapshot row per contact for run_date. Returns row count."""
    db.execute(delete(RfmSnapshot).where(RfmSnapshot.run_date == run_date))

    rows = []
    for _, row in scored.iterrows():
        guess = guesses[row["contact_id"]]
        recency = _none_if_nan(row.get("recency_days"))
        rows.append(RfmSnapshot(
            contact_id=row["contact_id"],
            run_date=run_date,
            recency_days=int(recency) if recency is not None else None,
            order_count=int(row["order_count"]),
            total_amount=int(row["total_amount"]),
            touch_count=int(row["touch_count"]),
            r_score=int(row["R"]),
            f_score=int(row["F"]),
            m_score=int(row["M"]),
            e_score=int(row["E"]),
            segment=row["rfm_segment"],
            persona_guess=guess.likely_persona,
            persona_confidence=guess.confidence,
            lead_pillar=guess.lead_pillar,
            journey_stage=guess.journey_stage,
        ))
    db.add_all(rows)
    db.flush()
    return len(rows)


def refresh_contacts_cache(db: Session, contacts: list[dict]) -> int:
    """Upserts the denormalized contact info the dashboard displays."""
    now = datetime.now(timezone.utc)
    existing = {c.contact_id: c for c in db.query(ContactCache).all()}
    count = 0
    for c in contacts:
        cid = str(c["id"])
        cached = existing.get(cid)
        if cached is None:
            cached = ContactCache(contact_id=cid)
            db.add(cached)
        cached.display_name = c.get("name")
        cached.phone = c.get("phone")
        cached.species = c.get("species")
        cached.updated_at = now
        count += 1
    db.flush()
    return count
