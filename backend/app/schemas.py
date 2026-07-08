"""Pydantic response/request schemas for the API contract (build plan Part 6)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# --- auth ---------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str
    language_pref: str
    numerals_pref: str


class PrefsUpdate(BaseModel):
    language_pref: str | None = Field(None, pattern="^(fa|en)$")
    numerals_pref: str | None = Field(None, pattern="^(western|persian)$")


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field("viewer", pattern="^(admin|viewer)$")


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# --- overview / meta ------------------------------------------------------

class SegmentCount(BaseModel):
    segment: str
    count: int


class PersonaCount(BaseModel):
    persona: str
    confirmed: int
    inferred: int
    count: int


class OverviewOut(BaseModel):
    run_date: date | None
    total_contacts: int
    segments: list[SegmentCount]


class PersonaOverviewOut(BaseModel):
    run_date: date | None
    personas: list[PersonaCount]


# --- contacts -------------------------------------------------------------

class ContactRow(BaseModel):
    contact_id: str
    display_name: str | None
    phone: str | None
    species: str | None
    segment: str | None
    persona_guess: str | None
    persona_confidence: str | None
    journey_stage: str | None
    lead_pillar: str | None
    r_score: int | None
    f_score: int | None
    m_score: int | None
    e_score: int | None
    recency_days: int | None
    order_count: int | None
    total_amount: int | None
    touch_count: int | None
    run_date: date | None


class ContactListOut(BaseModel):
    items: list[ContactRow]
    total: int
    page: int
    page_size: int


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    run_date: date
    recency_days: int | None
    order_count: int | None
    total_amount: int | None
    touch_count: int | None
    r_score: int | None
    f_score: int | None
    m_score: int | None
    e_score: int | None
    segment: str | None
    persona_guess: str | None
    persona_confidence: str | None
    lead_pillar: str | None
    journey_stage: str | None


class ContactDetailOut(BaseModel):
    contact_id: str
    display_name: str | None
    phone: str | None
    species: str | None
    latest: SnapshotOut | None
    history: list[SnapshotOut]


# --- trends -----------------------------------------------------------------

class TrendPoint(BaseModel):
    run_date: date
    segment: str
    count: int


class MigrationCell(BaseModel):
    from_segment: str
    to_segment: str
    count: int


class TrendsOut(BaseModel):
    series: list[TrendPoint]
    run_dates: list[date]
    migration: list[MigrationCell]
    from_date: date | None
    to_date: date | None


# --- sync ---------------------------------------------------------------

class SyncRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    trigger: str
    contacts_count: int | None
    orders_count: int | None
    calls_count: int | None
    sms_count: int | None
    error_message: str | None
