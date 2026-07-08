"""
RFM+E scoring engine.

Standard RFM (Recency, Frequency, Monetary) answers "how good a customer is
this, purely on purchases." Because Navatel is a unified CRM with call and
SMS logs, we add a fourth axis -- Engagement -- so the model also reflects
how responsive/reachable a customer currently is. This matters a lot for
Bamipet specifically: نگار-type guardians often generate high engagement
(calls, DM-equivalent questions) before their first or second purchase --
pure transactional RFM would miss them entirely as "low value."

Output: one row per contact with R/F/M/E scores (1-5 quintiles), a combined
segment label, and the raw metrics needed to sanity-check the label.
"""
from datetime import datetime, timedelta
import pandas as pd

from config import LOOKBACK_DAYS, RECENCY_REFERENCE


def _reference_date() -> datetime:
    return RECENCY_REFERENCE or datetime.utcnow()


def build_customer_table(contacts: list, orders: list, calls: list, sms: list) -> pd.DataFrame:
    """Joins raw Navatel records into one row per contact with the metrics
    RFM+E needs. Field names below (id, contact_id, amount, created_at, ...)
    are placeholders -- rename to match Navatel's real schema once known."""
    cutoff = _reference_date() - timedelta(days=LOOKBACK_DAYS)

    contacts_df = pd.DataFrame(contacts)
    orders_df = pd.DataFrame(orders)
    calls_df = pd.DataFrame(calls)
    sms_df = pd.DataFrame(sms)

    for df, date_col in [(orders_df, "created_at"), (calls_df, "created_at"), (sms_df, "created_at")]:
        if not df.empty:
            df[date_col] = pd.to_datetime(df[date_col])

    if not orders_df.empty:
        orders_df = orders_df[orders_df["created_at"] >= cutoff]
    if not calls_df.empty:
        calls_df = calls_df[calls_df["created_at"] >= cutoff]
    if not sms_df.empty:
        sms_df = sms_df[sms_df["created_at"] >= cutoff]

    # --- Recency & Frequency & Monetary, from orders ---
    if orders_df.empty:
        rfm = pd.DataFrame(columns=["contact_id", "last_order_date", "order_count", "total_amount"])
    else:
        rfm = orders_df.groupby("contact_id").agg(
            last_order_date=("created_at", "max"),
            order_count=("id", "count"),
            total_amount=("amount", "sum"),
        ).reset_index()

    # --- Engagement, from calls + sms (count + recency of any inbound/outbound contact) ---
    touch_frames = []
    if not calls_df.empty:
        touch_frames.append(calls_df[["contact_id", "created_at"]])
    if not sms_df.empty:
        touch_frames.append(sms_df[["contact_id", "created_at"]])

    if touch_frames:
        touches = pd.concat(touch_frames, ignore_index=True)
        engagement = touches.groupby("contact_id").agg(
            last_touch_date=("created_at", "max"),
            touch_count=("created_at", "count"),
        ).reset_index()
    else:
        engagement = pd.DataFrame(columns=["contact_id", "last_touch_date", "touch_count"])

    # --- Merge onto full contact list (so zero-order / zero-touch contacts are still scored) ---
    base = contacts_df[["id"]].rename(columns={"id": "contact_id"}) if not contacts_df.empty else pd.DataFrame(columns=["contact_id"])
    table = base.merge(rfm, on="contact_id", how="left").merge(engagement, on="contact_id", how="left")

    now = _reference_date()
    table["recency_days"] = (now - table["last_order_date"]).dt.days
    table["order_count"] = table["order_count"].fillna(0)
    table["total_amount"] = table["total_amount"].fillna(0)
    table["touch_count"] = table["touch_count"].fillna(0)
    table["engagement_recency_days"] = (now - table["last_touch_date"]).dt.days

    return table


def _quintile_score(series: pd.Series, ascending_is_better: bool) -> pd.Series:
    """Splits a metric into 1-5 score bands. For recency, lower is better
    (score 5 = most recent), so we invert the rank direction there."""
    ranks = series.rank(method="first", ascending=ascending_is_better)
    try:
        return pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)
    except ValueError:
        # Not enough distinct values for 5 clean bins (small or sparse dataset) -- fall back to fewer bins
        n_bins = min(5, series.nunique())
        n_bins = max(n_bins, 1)
        return pd.qcut(ranks, n_bins, labels=range(1, n_bins + 1), duplicates="drop").astype(int)


def score_rfm(table: pd.DataFrame) -> pd.DataFrame:
    df = table.copy()
    # Customers who never ordered get the worst possible R/F/M scores, not NaN
    df["recency_days"] = df["recency_days"].fillna(LOOKBACK_DAYS * 2)
    df["engagement_recency_days"] = df["engagement_recency_days"].fillna(LOOKBACK_DAYS * 2)

    df["R"] = _quintile_score(df["recency_days"], ascending_is_better=True)   # fewer days = higher score
    df["F"] = _quintile_score(df["order_count"], ascending_is_better=False)   # more orders = higher score
    df["M"] = _quintile_score(df["total_amount"], ascending_is_better=False)  # more spend = higher score
    df["E"] = _quintile_score(
        df["touch_count"] - (df["engagement_recency_days"] / LOOKBACK_DAYS),  # frequent + recent touches score highest
        ascending_is_better=False,
    )

    df["rfm_segment"] = df.apply(_label_segment, axis=1)
    return df


def _label_segment(row) -> str:
    """Standard RFM segment naming, conventional in CRM analytics -- these
    are internal labels for the team, not customer-facing anywhere."""
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
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f >= 4 and m >= 4:
        return "Can't Lose Them"
    if r <= 2 and f <= 2 and m <= 2:
        return "Hibernating / Lost"
    return "About To Sleep"
