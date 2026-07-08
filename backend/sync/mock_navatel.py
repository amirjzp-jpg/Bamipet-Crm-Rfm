"""
Deterministic mock Navatel client — the default data source until real
credentials exist (NAVATEL_MODE=mock).

Generates ~420 contacts across eight behavioral archetypes tuned so that:
  * every RFM segment and every persona-inference path gets exercised,
  * monthly historical re-scoring (the seed script) shows real segment
    migration (e.g. loyal customers decaying into At Risk), and
  * amounts/names/phones look like real Bamipet data (Toman, Persian names)
    so the dashboard demos honestly.

Deterministic: same day → same dataset (seeded RNG, dates relative to
today's midnight), so tests and repeated syncs are stable.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

_FIRST_NAMES = [
    "نگار", "سارا", "کیان", "امیر", "مریم", "علی", "زهرا", "رضا", "شیما", "حسین",
    "الهام", "مهدی", "نازنین", "پارسا", "لیلا", "آرش", "فاطمه", "سینا", "مینا", "بهزاد",
    "غزل", "کاوه", "پریسا", "فرهاد", "آیدا", "بابک", "شادی", "پویا", "ترانه", "هومن",
]
_LAST_NAMES = [
    "محمدی", "حسینی", "رضایی", "کریمی", "موسوی", "احمدی", "جعفری", "نوروزی", "قاسمی", "صادقی",
    "کاظمی", "رحیمی", "عباسی", "طاهری", "یوسفی", "شریفی", "زارعی", "اکبری", "نعمتی", "فرهادی",
]

# archetype -> (share, config)
_ARCHETYPES: list[tuple[str, float]] = [
    ("champion", 0.08),      # orders every 3-5 weeks, high spend, some touches
    ("loyal", 0.14),         # orders every 5-8 weeks, medium spend
    ("negar_new", 0.18),     # joined recently, 1-2 orders, MANY calls/sms (nervous first-timer)
    ("kian_dog", 0.10),      # dog guardian: bigger baskets, steady online orders
    ("amir", 0.12),          # 1-3 decisive high-value orders, near-zero touches
    ("decaying", 0.13),      # was loyal, stopped ordering ~3-5 months ago (At Risk arc)
    ("hibernating", 0.16),   # 1-2 orders long ago, silent since
    ("prospect", 0.09),      # zero orders, a few calls — the "worst bands, not dropped" case
]


def _today_midnight() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


class MockNavatelClient:
    """Drop-in stand-in for NavatelClient — same five methods, same
    canonical field names, no network."""

    def __init__(self, n_contacts: int = 420, seed: int = 42, now: datetime | None = None):
        self.now = now or _today_midnight()
        rng = random.Random(seed)
        self._contacts: list[dict] = []
        self._orders: list[dict] = []
        self._calls: list[dict] = []
        self._sms: list[dict] = []
        self._writebacks: list[tuple[str, str, Any]] = []  # recorded, for tests/inspection
        self._generate(n_contacts, rng)

    # --- generation --------------------------------------------------------

    def _generate(self, n_contacts: int, rng: random.Random) -> None:
        order_seq = call_seq = sms_seq = 0
        archetype_pool: list[str] = []
        for name, share in _ARCHETYPES:
            archetype_pool += [name] * round(share * n_contacts)
        while len(archetype_pool) < n_contacts:
            archetype_pool.append("loyal")
        rng.shuffle(archetype_pool)

        for i in range(n_contacts):
            cid = f"C{i + 1:04d}"
            arch = archetype_pool[i]
            species = "dog" if arch == "kian_dog" else ("dog" if rng.random() < 0.05 else "cat")
            self._contacts.append({
                "id": cid,
                "name": f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}",
                "phone": f"09{rng.choice(['12', '35', '19', '02', '90'])}{rng.randint(1000000, 9999999)}",
                "species": species,
            })

            def add_order(days_ago: float, lo: int, hi: int):
                nonlocal order_seq
                order_seq += 1
                self._orders.append({
                    "id": f"O{order_seq:05d}",
                    "contact_id": cid,
                    "amount": rng.randint(lo // 1000, hi // 1000) * 1000,  # Toman, round to 1k
                    "created_at": (self.now - timedelta(days=days_ago, hours=rng.randint(8, 21))).isoformat(),
                })

            def add_touch(days_ago: float, kind: str):
                nonlocal call_seq, sms_seq
                ts = (self.now - timedelta(days=days_ago, hours=rng.randint(8, 21))).isoformat()
                if kind == "call":
                    call_seq += 1
                    self._calls.append({"id": f"L{call_seq:05d}", "contact_id": cid, "created_at": ts})
                else:
                    sms_seq += 1
                    self._sms.append({"id": f"S{sms_seq:05d}", "contact_id": cid, "created_at": ts})

            if arch == "champion":
                d = rng.uniform(2, 18)
                while d < 540:
                    add_order(d, 1_800_000, 4_500_000)
                    if rng.random() < 0.35:
                        add_touch(d + rng.uniform(-2, 2), rng.choice(["call", "sms"]))
                    d += rng.uniform(20, 36)
            elif arch == "loyal":
                d = rng.uniform(5, 30)
                while d < 540:
                    add_order(d, 900_000, 2_600_000)
                    if rng.random() < 0.2:
                        add_touch(d + rng.uniform(-2, 2), rng.choice(["call", "sms"]))
                    d += rng.uniform(35, 60)
            elif arch == "negar_new":
                joined = rng.uniform(10, 65)
                for _ in range(rng.randint(1, 2)):
                    add_order(rng.uniform(2, min(joined, 40)), 700_000, 1_800_000)
                for _ in range(rng.randint(5, 14)):  # the anxious-question pattern
                    add_touch(rng.uniform(0, joined), rng.choice(["call", "call", "sms"]))
            elif arch == "kian_dog":
                d = rng.uniform(3, 25)
                while d < 480:
                    add_order(d, 2_200_000, 6_500_000)  # dogs eat more
                    if rng.random() < 0.25:
                        add_touch(d + rng.uniform(-2, 2), "sms")
                    d += rng.uniform(25, 45)
            elif arch == "amir":
                # decisive: one or two big consolidated baskets, near-zero touches
                for _ in range(rng.randint(1, 2)):
                    add_order(rng.uniform(10, 240), 5_500_000, 12_000_000)
                if rng.random() < 0.25:
                    add_touch(rng.uniform(10, 240), "sms")
            elif arch == "decaying":
                stop = rng.uniform(95, 160)  # last order 3-5 months ago
                d = stop
                while d < 620:
                    add_order(d, 1_100_000, 3_000_000)
                    d += rng.uniform(30, 55)
                if rng.random() < 0.4:
                    add_touch(rng.uniform(stop, stop + 60), "call")
            elif arch == "hibernating":
                for _ in range(rng.randint(1, 2)):
                    add_order(rng.uniform(250, 600), 600_000, 1_500_000)
            elif arch == "prospect":
                for _ in range(rng.randint(1, 5)):
                    add_touch(rng.uniform(1, 120), rng.choice(["call", "sms"]))

    # --- NavatelClientProtocol ---------------------------------------------

    def get_contacts(self) -> list[dict]:
        return [dict(c) for c in self._contacts]

    def get_orders(self) -> list[dict]:
        return [dict(o) for o in self._orders]

    def get_call_logs(self) -> list[dict]:
        return [dict(c) for c in self._calls]

    def get_sms_logs(self) -> list[dict]:
        return [dict(s) for s in self._sms]

    def update_contact_field(self, contact_id: str, field_name: str, value: Any) -> None:
        self._writebacks.append((contact_id, field_name, value))
