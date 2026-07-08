"""
RFM+E scoring engine.

Standard RFM (Recency, Frequency, Monetary) answers "how good a customer is
this, purely on purchases." Because Navatel is a unified CRM with call and
SMS logs, we add a fourth axis — Engagement — so the model also reflects
how responsive/reachable a customer currently is. This matters a lot for
Bamipet specifically: نگار-type guardians often generate high engagement
(calls, DM-equivalent questions) before their first or second purchase —
pure transactional RFM would miss them entirely as "low value."

Output: one row per contact with R/F/M/E scores (1-5 quintiles), a combined
segment label, and the raw metrics needed to sanity-check the label.

Hardened from the original prototype:
  * reference_date is an explicit parameter (tz-naive UTC), so historical
    re-scoring (seed script, backfills) is first-class rather than a global.
  * "Can't Lose Them" is checked before "At Risk" — in the original rule
    order it was unreachable (every r<=2,f>=4 row hit "At Risk" first).
  * empty inputs (no contacts / no orders / no touches) all degrade cleanly.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd


def utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def build_customer_table(
    contacts: list[dict],
    orders: list[dict],
    calls: list[dict],
    sms: list[dict],
    reference_date: datetime | None = None,
    lookback_days: int = 365,
) -> pd.DataFrame:
    """Joins raw (already alias-normalized) Navatel records into one row per
    contact with the metrics RFM+E needs. Expects canonical field names:
    contacts: id / name / phone / species — orders: id / contact_id /
    amount / created_at — calls & sms: contact_id / created_at."""
    now = reference_date or utc_naive_now()
    cutoff = now - timedelta(days=lookback_days)

    contacts_df = pd.DataFrame(contacts)
    orders_df = pd.DataFrame(orders)
    calls_df = pd.DataFrame(calls)
    sms_df = pd.DataFrame(sms)

    for df in (orders_df, calls_df, sms_df):
        if not df.empty:
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)

    # Only events the reference date could have "seen" — critical for
    # historical re-scoring, where future events must not leak backwards.
    if not orders_df.empty:
        orders_df = orders_df[(orders_df["created_at"] >= cutoff) & (orders_df["created_at"] <= now)]
    if not calls_df.empty:
        calls_df = calls_df[(calls_df["created_at"] >= cutoff) & (calls_df["created_at"] <= now)]
    if not sms_df.empty:
        sms_df = sms_df[(sms_df["created_at"] >= cutoff) & (sms_df["created_at"] <= now)]

    # --- Recency & Frequency & Monetary, from orders ---
    if orders_df.empty:
        rfm = pd.DataFrame(columns=["contact_id", "last_order_date", "order_count", "total_amount"])
    else:
        rfm = orders_df.groupby("contact_id").agg(
            last_order_date=("created_at", "max"),
            order_count=("id", "count"),
            total_amount=("amount", "sum"),
        ).reset_index()

    # --- Engagement, from calls + sms (count + recency of any touch) ---
    touch_frames = [df[["contact_id", "created_at"]] for df in (calls_df, sms_df) if not df.empty]
    if touch_frames:
        touches = pd.concat(touch_frames, ignore_index=True)
        engagement = touches.groupby("contact_id").agg(
            last_touch_date=("created_at", "max"),
            touch_count=("created_at", "count"),
        ).reset_index()
    else:
        engagement = pd.DataFrame(columns=["contact_id", "last_touch_date", "touch_count"])

    # --- Merge onto the full contact list, so zero-order / zero-touch
    # contacts are still scored (they land in the worst bands, not dropped).
    if contacts_df.empty:
        return pd.DataFrame(columns=[
            "contact_id", "last_order_date", "order_count", "total_amount",
            "last_touch_date", "touch_count", "recency_days", "engagement_recency_days", "species",
        ])
    base = contacts_df.rename(columns={"id": "contact_id"})
    keep = [c for c in ("contact_id", "species") if c in base.columns]
    base = base[keep]
    if "species" not in base.columns:
        base["species"] = None

    table = base.merge(rfm, on="contact_id", how="left").merge(engagement, on="contact_id", how="left")
    for col, empty_default in (
        ("last_order_date", pd.NaT), ("order_count", 0), ("total_amount", 0),
        ("last_touch_date", pd.NaT), ("touch_count", 0),
    ):
        if col not in table.columns:
            table[col] = empty_default

    table["last_order_date"] = pd.to_datetime(table["last_order_date"])
    table["last_touch_date"] = pd.to_datetime(table["last_touch_date"])
    table["recency_days"] = (now - table["last_order_date"]).dt.days
    table["order_count"] = pd.to_numeric(table["order_count"], errors="coerce").fillna(0).astype(int)
    table["total_amount"] = pd.to_numeric(table["total_amount"], errors="coerce").fillna(0)
    table["touch_count"] = pd.to_numeric(table["touch_count"], errors="coerce").fillna(0).astype(int)
    table["engagement_recency_days"] = (now - table["last_touch_date"]).dt.days
    table.attrs["lookback_days"] = lookback_days
    return table


def _quintile_score(series: pd.Series, higher_is_better: bool) -> pd.Series:
    """Splits a metric into 1-5 score bands, 5 = best.

    Tie-aware by construction: identical metric values always receive the
    identical score (rank method="average" + duplicate-edge collapsing), so
    a contact with 1 order can never outrank another contact with 1 order —
    a requirement of the spec's auditability goal ("every score is
    explainable from raw data"). With heavy ties (e.g. half the base has 0
    orders) fewer than 5 distinct bands may exist; the bands that do exist
    are stretched back onto the 1-5 scale so 1 stays "worst" and 5 "best".

    For recency, fewer days is better → pass higher_is_better=False.
    """
    if series.empty:
        return pd.Series(dtype=int)
    ranks = series.rank(method="average", ascending=higher_is_better)  # best values → highest rank
    if ranks.nunique() == 1:
        return pd.Series([3] * len(series), index=series.index, dtype=int)  # no signal → neutral
    bins = pd.qcut(ranks, 5, labels=False, duplicates="drop")
    n_bins = int(bins.max()) + 1
    if n_bins == 1:
        return pd.Series([3] * len(series), index=series.index, dtype=int)
    return (1 + (bins * 4 / (n_bins - 1))).round().astype(int)


def score_rfm(table: pd.DataFrame, lookback_days: int | None = None) -> pd.DataFrame:
    df = table.copy()
    if df.empty:
        for col in ("R", "F", "M", "E"):
            df[col] = pd.Series(dtype=int)
        df["rfm_segment"] = pd.Series(dtype=str)
        return df

    lookback = lookback_days or table.attrs.get("lookback_days", 365)
    # Customers who never ordered/touched get worst-possible recency, not NaN
    df["recency_days"] = df["recency_days"].fillna(lookback * 2)
    df["engagement_recency_days"] = df["engagement_recency_days"].fillna(lookback * 2)

    df["R"] = _quintile_score(df["recency_days"], higher_is_better=False)   # fewer days = higher score
    df["F"] = _quintile_score(df["order_count"], higher_is_better=True)     # more orders = higher score
    df["M"] = _quintile_score(df["total_amount"], higher_is_better=True)    # more spend = higher score
    df["E"] = _quintile_score(
        df["touch_count"] - (df["engagement_recency_days"] / lookback),     # frequent + recent touches
        higher_is_better=True,
    )

    df["rfm_segment"] = df.apply(_label_segment, axis=1)
    return df


def _label_segment(row) -> str:
    """Standard RFM segment naming, conventional in CRM analytics — these
    are internal labels for the team, not customer-facing anywhere.
    Rule order matters: most specific first."""
    r, f, m = row["R"], row["F"], row["M"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "New Customers"
    if r >= 3 and f <= 2 and m >= 3:
        return "Promising"
    if r == 3 and f == 3:
        return "Needs Attention"
    if r <= 2 and f >= 4 and m >= 4:
        return "Can't Lose Them"   # checked BEFORE At Risk — subset rule first
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2 and m <= 2:
        return "Hibernating / Lost"
    return "About To Sleep"
