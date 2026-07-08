"""Persona inference paths + warehouse idempotency."""
from datetime import date, datetime

from sync.job import run_sync
from sync.mock_navatel import MockNavatelClient
from sync.persona_mapper import guess_persona
from app.config import get_settings
from app.models import RfmSnapshot, SyncRun


def _row(segment="Loyal Customers", R=3, F=3, M=3, E=3):
    return {"rfm_segment": segment, "R": R, "F": F, "M": M, "E": E}


def test_species_dog_overrides_everything():
    g = guess_persona(_row(segment="Hibernating / Lost"), species="dog")
    assert g.likely_persona == "کیان"
    assert g.confidence == "confirmed"


def test_negar_needs_new_and_engaged():
    assert guess_persona(_row(segment="New Customers", E=5, F=1)).likely_persona == "نگار"
    assert guess_persona(_row(segment="New Customers", E=2, F=1)).likely_persona == "نامشخص"


def test_sara_frequent_high_spend_low_touch():
    assert guess_persona(_row(F=5, M=5, E=2)).likely_persona == "سارا"
    assert guess_persona(_row(F=5, M=5, E=5)).likely_persona != "سارا"


def test_amir_decisive_low_touch():
    assert guess_persona(_row(F=1, M=5, E=1)).likely_persona == "امیر"


def test_win_back_pillar_never_mentions_discount_positively():
    g = guess_persona(_row(segment="At Risk"))
    assert "۴" in g.lead_pillar and "تخفیف" not in g.lead_pillar.replace("بدونِ تخفیف", "")


def test_sync_idempotent_per_run_date(db):
    client = MockNavatelClient(n_contacts=40)
    settings = get_settings()
    ref = datetime(2026, 6, 1)

    run1 = run_sync(db, client=client, settings=settings, reference_date=ref, trigger="manual")
    assert run1.status == "success", run1.error_message
    count1 = db.query(RfmSnapshot).filter_by(run_date=date(2026, 6, 1)).count()
    assert count1 == 40

    # Re-running the same day replaces, never duplicates
    run2 = run_sync(db, client=client, settings=settings, reference_date=ref, trigger="manual")
    assert run2.status == "success"
    count2 = db.query(RfmSnapshot).filter_by(run_date=date(2026, 6, 1)).count()
    assert count2 == 40
    assert db.query(SyncRun).count() >= 2  # both runs audited


def test_failed_sync_is_recorded_not_raised(db):
    class BrokenClient:
        def get_contacts(self):
            raise RuntimeError("gateway down")

    run = run_sync(db, client=BrokenClient(), settings=get_settings(),
                   reference_date=datetime(2026, 6, 2), trigger="manual")
    assert run.status == "failed"
    assert "gateway down" in run.error_message
