"""API contract tests — auth, RBAC, filters, export, meta."""
from datetime import datetime

from app.config import get_settings
from app.database import SessionLocal
from sync.job import run_sync
from sync.mock_navatel import MockNavatelClient


def _seed_snapshots():
    db = SessionLocal()
    try:
        client = MockNavatelClient(n_contacts=60)
        for ref in (datetime(2026, 5, 1), datetime(2026, 7, 1)):
            run = run_sync(db, client=client, settings=get_settings(), reference_date=ref, trigger="seed")
            assert run.status == "success", run.error_message
    finally:
        db.close()


def test_login_rejects_bad_credentials(client):
    assert client.post("/api/v1/auth/login", json={"username": "testadmin", "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": "ghost", "password": "wrong"}).status_code == 401


def test_refresh_flow(client, admin_headers):
    login = client.post("/api/v1/auth/login", json={"username": "testadmin", "password": "testpass123"}).json()
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    # an access token is NOT usable as a refresh token
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": login["access_token"]}).status_code == 401


def test_all_data_routes_require_auth(client):
    for path in ("/api/v1/segments/overview", "/api/v1/personas/overview", "/api/v1/contacts",
                 "/api/v1/trends/segment-migration", "/api/v1/sync-runs", "/api/v1/export/contacts.csv"):
        assert client.get(path).status_code == 401, path


def test_admin_routes_forbidden_for_viewer(client, viewer_headers):
    assert client.get("/api/v1/admin/config", headers=viewer_headers).status_code == 403
    assert client.post("/api/v1/sync-runs/trigger", headers=viewer_headers).status_code == 403
    assert client.get("/api/v1/users", headers=viewer_headers).status_code == 403


def test_overview_and_contacts_flow(client, admin_headers):
    _seed_snapshots()

    overview = client.get("/api/v1/segments/overview", headers=admin_headers).json()
    assert overview["total_contacts"] == 60
    assert sum(s["count"] for s in overview["segments"]) == 60

    meta = client.get("/api/v1/segments/meta", headers=admin_headers).json()
    codes = {s["code"] for s in meta["segments"]}
    assert {s["segment"] for s in overview["segments"]} <= codes
    assert all("fa" in s and "color" in s for s in meta["segments"])

    # filter + paginate + sort
    listing = client.get("/api/v1/contacts", headers=admin_headers,
                         params={"page_size": 10, "sort": "total_amount", "order": "desc"}).json()
    assert listing["total"] == 60 and len(listing["items"]) == 10
    amounts = [i["total_amount"] or 0 for i in listing["items"]]
    assert amounts == sorted(amounts, reverse=True)

    seg = listing["items"][0]["segment"]
    filtered = client.get("/api/v1/contacts", headers=admin_headers, params={"segment": seg}).json()
    assert all(i["segment"] == seg for i in filtered["items"])

    # search by name fragment
    name = listing["items"][0]["display_name"].split()[0]
    search = client.get("/api/v1/contacts", headers=admin_headers, params={"search": name}).json()
    assert search["total"] >= 1

    # drill-down carries both run dates
    cid = listing["items"][0]["contact_id"]
    detail = client.get(f"/api/v1/contacts/{cid}", headers=admin_headers).json()
    assert len(detail["history"]) == 2
    assert detail["latest"]["run_date"] == "2026-07-01"

    assert client.get("/api/v1/contacts/NOPE", headers=admin_headers).status_code == 404


def test_trends_and_export(client, admin_headers):
    trends = client.get("/api/v1/trends/segment-migration", headers=admin_headers).json()
    assert trends["run_dates"] == ["2026-05-01", "2026-07-01"]
    assert trends["series"]
    total_moved = sum(m["count"] for m in trends["migration"])
    assert 0 <= total_moved <= 60

    csv_resp = client.get("/api/v1/export/contacts.csv", headers=admin_headers)
    assert csv_resp.status_code == 200
    body = csv_resp.text
    assert body.startswith("﻿contact_id") and body.count("\n") >= 61  # BOM + header + 60 rows


def test_prefs_and_user_management(client, admin_headers):
    me = client.patch("/api/v1/me/prefs", headers=admin_headers,
                      json={"language_pref": "en", "numerals_pref": "persian"}).json()
    assert (me["language_pref"], me["numerals_pref"]) == ("en", "persian")

    created = client.post("/api/v1/users", headers=admin_headers,
                          json={"username": "newbie", "password": "longenough1", "role": "viewer"})
    assert created.status_code == 201
    assert client.post("/api/v1/users", headers=admin_headers,
                       json={"username": "newbie", "password": "longenough1", "role": "viewer"}).status_code == 409
    users = client.get("/api/v1/users", headers=admin_headers).json()
    assert any(u["username"] == "newbie" for u in users)
    uid = next(u["id"] for u in users if u["username"] == "newbie")
    assert client.delete(f"/api/v1/users/{uid}", headers=admin_headers).status_code == 204
