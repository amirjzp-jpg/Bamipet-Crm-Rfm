"""Customer table (filter/sort/paginate), drill-down history, CSV export."""
from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ContactCache, RfmSnapshot
from app.schemas import ContactDetailOut, ContactListOut, ContactRow, SnapshotOut

router = APIRouter(tags=["contacts"], dependencies=[Depends(get_current_user)])

# whitelist: query-param sort key -> ORDER BY column
_SORTABLE = {
    "display_name": ContactCache.display_name,
    "segment": RfmSnapshot.segment,
    "persona_guess": RfmSnapshot.persona_guess,
    "recency_days": RfmSnapshot.recency_days,
    "order_count": RfmSnapshot.order_count,
    "total_amount": RfmSnapshot.total_amount,
    "touch_count": RfmSnapshot.touch_count,
    "r_score": RfmSnapshot.r_score,
    "f_score": RfmSnapshot.f_score,
    "m_score": RfmSnapshot.m_score,
    "e_score": RfmSnapshot.e_score,
}


def _latest_run_date(db: Session) -> date | None:
    return db.scalar(select(func.max(RfmSnapshot.run_date)))


def _filtered_query(
    run_date: date,
    segment: str | None,
    persona: str | None,
    journey_stage: str | None,
    search: str | None,
) -> Select:
    q = (
        select(RfmSnapshot, ContactCache)
        .join(ContactCache, ContactCache.contact_id == RfmSnapshot.contact_id, isouter=True)
        .where(RfmSnapshot.run_date == run_date)
    )
    if segment:
        q = q.where(RfmSnapshot.segment == segment)
    if persona:
        q = q.where(RfmSnapshot.persona_guess == persona)
    if journey_stage:
        q = q.where(RfmSnapshot.journey_stage == journey_stage)
    if search:
        like = f"%{search.strip()}%"
        q = q.where(or_(
            ContactCache.display_name.ilike(like),
            ContactCache.phone.ilike(like),
            RfmSnapshot.contact_id.ilike(like),
        ))
    return q


def _to_row(snap: RfmSnapshot, cache: ContactCache | None) -> ContactRow:
    return ContactRow(
        contact_id=snap.contact_id,
        display_name=cache.display_name if cache else None,
        phone=cache.phone if cache else None,
        species=cache.species if cache else None,
        segment=snap.segment,
        persona_guess=snap.persona_guess,
        persona_confidence=snap.persona_confidence,
        journey_stage=snap.journey_stage,
        lead_pillar=snap.lead_pillar,
        r_score=snap.r_score, f_score=snap.f_score, m_score=snap.m_score, e_score=snap.e_score,
        recency_days=snap.recency_days,
        order_count=snap.order_count,
        total_amount=int(snap.total_amount) if snap.total_amount is not None else None,
        touch_count=snap.touch_count,
        run_date=snap.run_date,
    )


@router.get("/contacts", response_model=ContactListOut)
def list_contacts(
    segment: str | None = None,
    persona: str | None = None,
    journey_stage: str | None = None,
    search: str | None = None,
    sort: str = Query("total_amount", description=f"one of: {', '.join(_SORTABLE)}"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    run_date = _latest_run_date(db)
    if run_date is None:
        return ContactListOut(items=[], total=0, page=page, page_size=page_size)

    q = _filtered_query(run_date, segment, persona, journey_stage, search)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0

    sort_col = _SORTABLE.get(sort, RfmSnapshot.total_amount)
    q = q.order_by(sort_col.desc().nullslast() if order == "desc" else sort_col.asc().nullsfirst())
    q = q.offset((page - 1) * page_size).limit(page_size)

    items = [_to_row(snap, cache) for snap, cache in db.execute(q).all()]
    return ContactListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/contacts/{contact_id}", response_model=ContactDetailOut)
def contact_detail(contact_id: str, db: Session = Depends(get_db)):
    history = db.scalars(
        select(RfmSnapshot)
        .where(RfmSnapshot.contact_id == contact_id)
        .order_by(RfmSnapshot.run_date)
    ).all()
    cache = db.get(ContactCache, contact_id)
    if not history and cache is None:
        raise HTTPException(404, "Contact not found")
    return ContactDetailOut(
        contact_id=contact_id,
        display_name=cache.display_name if cache else None,
        phone=cache.phone if cache else None,
        species=cache.species if cache else None,
        latest=SnapshotOut.model_validate(history[-1]) if history else None,
        history=[SnapshotOut.model_validate(s) for s in history],
    )


@router.get("/export/contacts.csv")
def export_contacts_csv(
    segment: str | None = None,
    persona: str | None = None,
    journey_stage: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    """Same filters as /contacts, streamed as UTF-8-BOM CSV (Excel opens
    Persian text correctly only with the BOM)."""
    run_date = _latest_run_date(db)
    header = ["contact_id", "name", "phone", "species", "segment", "persona_guess",
              "persona_confidence", "journey_stage", "lead_pillar", "R", "F", "M", "E",
              "recency_days", "order_count", "total_amount_toman", "touch_count", "run_date"]

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        buf.write("﻿")  # BOM for Excel
        writer.writerow(header)
        yield buf.getvalue()
        if run_date is None:
            return
        q = _filtered_query(run_date, segment, persona, journey_stage, search).order_by(RfmSnapshot.total_amount.desc())
        for snap, cache in db.execute(q).yield_per(500):
            buf.seek(0); buf.truncate(0)
            writer.writerow([
                snap.contact_id,
                cache.display_name if cache else "",
                cache.phone if cache else "",
                cache.species if cache else "",
                snap.segment, snap.persona_guess, snap.persona_confidence,
                snap.journey_stage, snap.lead_pillar,
                snap.r_score, snap.f_score, snap.m_score, snap.e_score,
                snap.recency_days, snap.order_count,
                int(snap.total_amount) if snap.total_amount is not None else "",
                snap.touch_count, snap.run_date.isoformat(),
            ])
            yield buf.getvalue()

    filename = f"bamipet-contacts-{run_date.isoformat() if run_date else 'empty'}.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
