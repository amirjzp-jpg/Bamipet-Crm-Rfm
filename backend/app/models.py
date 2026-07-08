"""Warehouse schema — build plan Part 2, verbatim in SQLAlchemy form.

rfm_snapshots is append-only per (contact_id, run_date): every sync run adds
one row per contact, never rewriting history, so the dashboard can show
segment movement over time. contacts_cache is a denormalized copy of the
contact info the dashboard needs (name/phone/species), refreshed on each
sync so page loads never hit Navatel live.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# SQLite (tests) needs Integer for autoincrement PKs; Postgres gets BIGSERIAL.
PKBigInt = BigInteger().with_variant(Integer, "sqlite")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RfmSnapshot(Base):
    __tablename__ = "rfm_snapshots"
    __table_args__ = (
        UniqueConstraint("contact_id", "run_date", name="uq_rfm_snapshots_contact_run"),
        Index("idx_rfm_snapshots_run_date", "run_date"),
        Index("idx_rfm_snapshots_contact", "contact_id", "run_date"),
        Index("idx_rfm_snapshots_segment", "run_date", "segment"),
    )

    id: Mapped[int] = mapped_column(PKBigInt, primary_key=True)
    contact_id: Mapped[str] = mapped_column(Text, nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    recency_days: Mapped[int | None] = mapped_column(Integer)
    order_count: Mapped[int | None] = mapped_column(Integer)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 0))  # Toman, whole units
    touch_count: Mapped[int | None] = mapped_column(Integer)
    r_score: Mapped[int | None] = mapped_column(SmallInteger)
    f_score: Mapped[int | None] = mapped_column(SmallInteger)
    m_score: Mapped[int | None] = mapped_column(SmallInteger)
    e_score: Mapped[int | None] = mapped_column(SmallInteger)
    segment: Mapped[str | None] = mapped_column(Text)
    persona_guess: Mapped[str | None] = mapped_column(Text)
    persona_confidence: Mapped[str | None] = mapped_column(Text)  # 'confirmed' | 'inferred'
    lead_pillar: Mapped[str | None] = mapped_column(Text)
    journey_stage: Mapped[str | None] = mapped_column(Text)


class ContactCache(Base):
    __tablename__ = "contacts_cache"

    contact_id: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    species: Mapped[str | None] = mapped_column(Text)   # 'cat' | 'dog' | NULL
    channel: Mapped[str | None] = mapped_column(Text)   # 'online' | 'in_store' | NULL
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(PKBigInt, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="running")  # running|success|failed
    trigger: Mapped[str] = mapped_column(Text, nullable=False, default="scheduled")  # scheduled|manual|seed
    contacts_count: Mapped[int | None] = mapped_column(Integer)
    orders_count: Mapped[int | None] = mapped_column(Integer)
    calls_count: Mapped[int | None] = mapped_column(Integer)
    sms_count: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PKBigInt, primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="viewer")  # 'admin' | 'viewer'
    language_pref: Mapped[str] = mapped_column(Text, nullable=False, default="fa")      # 'fa' | 'en'
    numerals_pref: Mapped[str] = mapped_column(Text, nullable=False, default="western")  # 'western' | 'persian'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
