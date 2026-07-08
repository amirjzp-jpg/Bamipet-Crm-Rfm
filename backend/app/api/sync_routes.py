"""Sync-run history, manual trigger, and the admin config debug view."""
from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import SyncRun
from app.schemas import SyncRunOut

router = APIRouter(tags=["sync"])

_sync_lock = threading.Lock()  # one manual sync at a time per API process


@router.get("/sync-runs", response_model=list[SyncRunOut], dependencies=[Depends(get_current_user)])
def list_sync_runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return db.scalars(select(SyncRun).order_by(SyncRun.id.desc()).limit(limit)).all()


def _run_sync_in_background():
    from sync.job import run_sync  # imported here so API workers stay light
    db = SessionLocal()
    try:
        run_sync(db, trigger="manual")
    finally:
        db.close()
        _sync_lock.release()


@router.post("/sync-runs/trigger", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_admin)])
def trigger_sync():
    if not _sync_lock.acquire(blocking=False):
        raise HTTPException(status.HTTP_409_CONFLICT, "A sync is already running")
    threading.Thread(target=_run_sync_in_background, daemon=True).start()
    return {"status": "started"}


@router.get("/admin/config", dependencies=[Depends(require_admin)])
def config_debug():
    """Read-only view of the active Navatel wiring for debugging field
    mappings. Never exposes the token itself."""
    s = get_settings()
    return {
        "navatel_mode": s.NAVATEL_MODE,
        "base_url": s.NAVATEL_BASE_URL,
        "token_configured": bool(s.NAVATEL_API_TOKEN),
        "endpoints": s.endpoints,
        "field_aliases": s.field_aliases,
        "lookback_days": s.LOOKBACK_DAYS,
        "writeback_enabled": s.ENABLE_WRITEBACK,
        "writeback_fields": [s.SEGMENT_FIELD_NAME, s.PERSONA_FIELD_NAME],
        "nightly_sync_at": f"{s.SYNC_CRON_HOUR:02d}:{s.SYNC_CRON_MINUTE:02d} Asia/Tehran",
    }
