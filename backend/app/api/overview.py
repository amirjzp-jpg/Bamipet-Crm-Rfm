"""Segment/persona overview + the meta registry the frontend styles from."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import RfmSnapshot
from app.schemas import OverviewOut, PersonaCount, PersonaOverviewOut, SegmentCount
from sync.segments import JOURNEY_STAGES, PERSONAS, SEGMENT_CODES, SEGMENTS

router = APIRouter(tags=["overview"], dependencies=[Depends(get_current_user)])


def latest_run_date(db: Session):
    return db.scalar(select(func.max(RfmSnapshot.run_date)))


@router.get("/segments/meta")
def segments_meta():
    """Single source of truth for segment/persona labels + colors (sync/segments.py)."""
    return {"segments": SEGMENTS, "personas": PERSONAS, "journey_stages": JOURNEY_STAGES}


@router.get("/segments/overview", response_model=OverviewOut)
def segments_overview(db: Session = Depends(get_db)):
    run_date = latest_run_date(db)
    if run_date is None:
        return OverviewOut(run_date=None, total_contacts=0, segments=[])
    rows = db.execute(
        select(RfmSnapshot.segment, func.count())
        .where(RfmSnapshot.run_date == run_date)
        .group_by(RfmSnapshot.segment)
    ).all()
    counts = {segment: count for segment, count in rows}
    ordered = [SegmentCount(segment=code, count=counts.get(code, 0)) for code in SEGMENT_CODES]
    return OverviewOut(run_date=run_date, total_contacts=sum(counts.values()), segments=ordered)


@router.get("/personas/overview", response_model=PersonaOverviewOut)
def personas_overview(db: Session = Depends(get_db)):
    run_date = latest_run_date(db)
    if run_date is None:
        return PersonaOverviewOut(run_date=None, personas=[])
    rows = db.execute(
        select(RfmSnapshot.persona_guess, RfmSnapshot.persona_confidence, func.count())
        .where(RfmSnapshot.run_date == run_date)
        .group_by(RfmSnapshot.persona_guess, RfmSnapshot.persona_confidence)
    ).all()
    by_persona: dict[str, dict[str, int]] = {}
    for persona, confidence, count in rows:
        bucket = by_persona.setdefault(persona or "نامشخص", {"confirmed": 0, "inferred": 0})
        bucket[confidence or "inferred"] += count
    personas = [
        PersonaCount(persona=p["code"],
                     confirmed=by_persona.get(p["code"], {}).get("confirmed", 0),
                     inferred=by_persona.get(p["code"], {}).get("inferred", 0),
                     count=sum(by_persona.get(p["code"], {"confirmed": 0, "inferred": 0}).values()))
        for p in PERSONAS
    ]
    return PersonaOverviewOut(run_date=run_date, personas=personas)
