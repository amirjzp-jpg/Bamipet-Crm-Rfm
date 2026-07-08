"""Segment counts over time + migration matrix between two run dates."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.auth import get_current_user
from app.database import get_db
from app.models import RfmSnapshot
from app.schemas import MigrationCell, TrendPoint, TrendsOut

router = APIRouter(tags=["trends"], dependencies=[Depends(get_current_user)])


@router.get("/trends/segment-migration", response_model=TrendsOut)
def segment_migration(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    run_dates = db.scalars(
        select(RfmSnapshot.run_date).distinct().order_by(RfmSnapshot.run_date)
    ).all()
    if not run_dates:
        return TrendsOut(series=[], run_dates=[], migration=[], from_date=None, to_date=None)

    # counts per (run_date, segment) — the time-series view
    series_rows = db.execute(
        select(RfmSnapshot.run_date, RfmSnapshot.segment, func.count())
        .group_by(RfmSnapshot.run_date, RfmSnapshot.segment)
        .order_by(RfmSnapshot.run_date)
    ).all()
    series = [TrendPoint(run_date=d, segment=s, count=c) for d, s, c in series_rows]

    # migration matrix between two snapshots (default: first vs latest)
    start = from_date if from_date in run_dates else run_dates[0]
    end = to_date if to_date in run_dates else run_dates[-1]
    migration: list[MigrationCell] = []
    if start != end:
        a, b = aliased(RfmSnapshot), aliased(RfmSnapshot)
        rows = db.execute(
            select(a.segment, b.segment, func.count())
            .select_from(a)
            .join(b, (a.contact_id == b.contact_id) & (b.run_date == end))
            .where(a.run_date == start)
            .group_by(a.segment, b.segment)
        ).all()
        migration = [
            MigrationCell(from_segment=f, to_segment=t, count=c)
            for f, t, c in rows if f != t  # only movement, not the stayed-put diagonal
        ]
        migration.sort(key=lambda m: -m.count)

    return TrendsOut(series=series, run_dates=list(run_dates), migration=migration,
                     from_date=start, to_date=end)
