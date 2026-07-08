"""Bamipet RFM API — FastAPI application entry point.

Serves the dashboard's data layer in front of the Postgres warehouse
(build plan Part 6). All business data routes require a JWT; interactive
docs live at /api/docs.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_routes, contacts, overview, sync_routes, trends
from app.config import get_settings

app = FastAPI(
    title="Bamipet RFM API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(overview.router, prefix=API_PREFIX)
app.include_router(contacts.router, prefix=API_PREFIX)
app.include_router(trends.router, prefix=API_PREFIX)
app.include_router(sync_routes.router, prefix=API_PREFIX)


@app.get("/api/health")
def health():
    return {"status": "ok"}
