"""Engine correctness: scoring direction, tie fairness, segment rules,
empty/small-data degradation."""
from datetime import datetime, timedelta

import pandas as pd

from sync.rfm_engine import build_customer_table, score_rfm, _quintile_score

NOW = datetime(2026, 7, 1)


def _mk_data():
    """5 contacts spanning the spectrum: champion, loyal, new+engaged (نگار
    shape), decayed, never-ordered prospect."""
    contacts = [{"id": f"C{i}", "name": f"n{i}", "phone": "09", "species": "cat"} for i in range(1, 6)]
    orders, calls, sms = [], [], []
    oid = 0

    def order(cid, days_ago, amount):
        nonlocal oid
        oid += 1
        orders.append({"id": f"O{oid}", "contact_id": cid, "amount": amount,
                       "created_at": (NOW - timedelta(days=days_ago)).isoformat()})

    # C1 champion: 10 recent orders, big amounts
    for d in range(5, 305, 30):
        order("C1", d, 3_000_000)
    # C2 loyal: 6 orders, medium
    for d in range(20, 320, 50):
        order("C2", d, 1_500_000)
    # C3 نگار: 1 recent order, many calls
    order("C3", 10, 900_000)
    for d in range(1, 40, 4):
        calls.append({"id": f"L{d}", "contact_id": "C3", "created_at": (NOW - timedelta(days=d)).isoformat()})
    # C4 decayed: 4 orders, all 5+ months old
    for d in range(160, 340, 45):
        order("C4", d, 1_200_000)
    # C5 prospect: no orders, 2 sms
    for d in (3, 9):
        sms.append({"id": f"S{d}", "contact_id": "C5", "created_at": (NOW - timedelta(days=d)).isoformat()})

    return contacts, orders, calls, sms


def test_scoring_direction_and_segments():
    contacts, orders, calls, sms = _mk_data()
    table = build_customer_table(contacts, orders, calls, sms, reference_date=NOW)
    scored = score_rfm(table).set_index("contact_id")

    champ, prospect = scored.loc["C1"], scored.loc["C5"]
    # Direction: the champion must outscore the prospect on R/F/M — this is
    # the exact inversion bug the prototype shipped with.
    assert champ["R"] > prospect["R"]
    assert champ["F"] > prospect["F"]
    assert champ["M"] > prospect["M"]
    assert champ["rfm_segment"] == "Champions"
    assert prospect["rfm_segment"] == "Hibernating / Lost"
    # نگار shape: recent + low frequency => New Customers, high engagement
    negar = scored.loc["C3"]
    assert negar["rfm_segment"] == "New Customers"
    assert negar["E"] == scored["E"].max()
    # Decayed contact must not land in a healthy segment
    assert scored.loc["C4"]["rfm_segment"] in ("At Risk", "About To Sleep", "Hibernating / Lost", "Can't Lose Them")


def test_ties_get_identical_scores():
    s = pd.Series([0, 0, 0, 0, 0, 0, 1, 2, 3, 10])
    scores = _quintile_score(s, higher_is_better=True)
    zero_scores = set(scores[s == 0])
    assert len(zero_scores) == 1, "identical raw values must share one score"
    assert scores[s == 10].iloc[0] == 5
    assert scores[s == 0].iloc[0] < scores[s == 1].iloc[0]


def test_empty_and_tiny_inputs():
    empty = build_customer_table([], [], [], [], reference_date=NOW)
    assert score_rfm(empty).empty

    one = build_customer_table([{"id": "C1", "name": "x", "phone": "1", "species": None}], [], [], [],
                               reference_date=NOW)
    scored = score_rfm(one)
    assert len(scored) == 1
    assert scored.iloc[0]["rfm_segment"]  # labels fine with a single neutral row


def test_future_events_do_not_leak_into_historical_scoring():
    contacts = [{"id": "C1", "name": "x", "phone": "1", "species": None}]
    orders = [{"id": "O1", "contact_id": "C1", "amount": 1000,
               "created_at": (NOW + timedelta(days=30)).isoformat()}]  # after ref date
    table = build_customer_table(contacts, orders, [], [], reference_date=NOW)
    assert table.iloc[0]["order_count"] == 0
