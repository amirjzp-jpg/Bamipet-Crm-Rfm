"""Shared fixtures: an isolated SQLite database per test session + an
authenticated API client. DATABASE_URL must be set to sqlite BEFORE app
imports, hence the env override at module import time."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_bamipet.db"
os.environ["SECRET_KEY"] = "test-secret"

import pytest
from fastapi.testclient import TestClient

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    if os.path.exists("./test_bamipet.db"):
        os.remove("./test_bamipet.db")


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_headers(client, _schema):
    session = SessionLocal()
    session.add(User(username="testadmin", password_hash=hash_password("testpass123"), role="admin"))
    session.add(User(username="testviewer", password_hash=hash_password("testpass123"), role="viewer"))
    session.commit()
    session.close()
    resp = client.post("/api/v1/auth/login", json={"username": "testadmin", "password": "testpass123"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="session")
def viewer_headers(client, admin_headers):
    resp = client.post("/api/v1/auth/login", json={"username": "testviewer", "password": "testpass123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
