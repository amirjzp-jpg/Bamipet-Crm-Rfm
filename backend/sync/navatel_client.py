"""
Navatel REST adapter — the bridge between Navatel's API Gateway and the
RFM engine's canonical record shape.

Design constraints (build plan Part 3):
  * Navatel's Swagger docs live behind login at cp.navatel.ir, so endpoint
    paths and field names here are configuration, not code. Going live is a
    .env edit: NAVATEL_MODE=live + base URL + token + endpoint paths +
    NAVATEL_FIELD_ALIASES (JSON mapping of canonical name -> real name).
  * Every fetch paginates until exhausted, retries 429/5xx with exponential
    backoff (honoring Retry-After when present), and normalizes each raw row
    through the alias map so downstream code only ever sees canonical names:
      contacts: id / name / phone / species
      orders:   id / contact_id / amount / created_at
      calls:    id / contact_id / created_at
      sms:      id / contact_id / created_at
  * Non-2xx after retries raises NavatelAPIError so the sync job records a
    clean failure in sync_runs instead of half-writing a snapshot.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Protocol

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class NavatelAPIError(Exception):
    """Raised when Navatel returns a non-recoverable error response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class NavatelClientProtocol(Protocol):
    """What the sync job needs from any Navatel client (live or mock)."""

    def get_contacts(self) -> list[dict]: ...
    def get_orders(self) -> list[dict]: ...
    def get_call_logs(self) -> list[dict]: ...
    def get_sms_logs(self) -> list[dict]: ...
    def update_contact_field(self, contact_id: str, field_name: str, value: Any) -> None: ...


def _apply_aliases(rows: list[dict], aliases: dict[str, str]) -> list[dict]:
    """Rename real API field names to canonical ones. Aliases map
    canonical -> real (e.g. {"amount": "mablagh_kol"}). Fields not present
    in a row come through as None so pandas gets consistent columns."""
    out = []
    for row in rows:
        out.append({canonical: row.get(real) for canonical, real in aliases.items()})
    return out


def _extract_items(payload: Any) -> list[dict]:
    """Navatel's exact envelope is unknown until the Swagger docs are read;
    accept the common shapes: bare list, {items|data|results|records: [...]}."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "data", "results", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise NavatelAPIError(f"Unrecognized response envelope: keys={list(payload)[:8] if isinstance(payload, dict) else type(payload)}")


class NavatelClient:
    """Live HTTP client against the real Navatel API Gateway."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        if not self.settings.NAVATEL_API_TOKEN:
            raise NavatelAPIError(
                "NAVATEL_API_TOKEN is not set. Generate a Bearer token in the "
                "cp.navatel.ir panel (API/webservice section) and set it in .env."
            )
        self._client = httpx.Client(
            base_url=self.settings.NAVATEL_BASE_URL,
            headers={"Authorization": f"Bearer {self.settings.NAVATEL_API_TOKEN}"},
            timeout=self.settings.NAVATEL_TIMEOUT_SECONDS,
        )

    # --- low-level -------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        retries = self.settings.NAVATEL_MAX_RETRIES
        for attempt in range(retries + 1):
            try:
                resp = self._client.request(method, path, **kwargs)
            except httpx.TransportError as exc:
                if attempt == retries:
                    raise NavatelAPIError(f"Network error calling {path}: {exc}") from exc
                time.sleep(2 ** attempt)
                continue
            if resp.status_code in (429,) or resp.status_code >= 500:
                if attempt == retries:
                    raise NavatelAPIError(
                        f"{method} {path} failed after {retries + 1} attempts: HTTP {resp.status_code}",
                        status_code=resp.status_code,
                    )
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                logger.warning("Navatel %s %s -> %s, retrying in %.0fs", method, path, resp.status_code, delay)
                time.sleep(delay)
                continue
            if resp.status_code >= 400:
                raise NavatelAPIError(
                    f"{method} {path} -> HTTP {resp.status_code}: {resp.text[:300]}",
                    status_code=resp.status_code,
                )
            return resp
        raise NavatelAPIError(f"{method} {path}: retry loop exhausted")  # unreachable

    def _get_all_pages(self, path: str) -> list[dict]:
        s = self.settings
        items: list[dict] = []
        page = 1
        while True:
            resp = self._request("GET", path, params={s.NAVATEL_PAGE_PARAM: page, s.NAVATEL_PAGE_SIZE_PARAM: s.NAVATEL_PAGE_SIZE})
            batch = _extract_items(resp.json())
            items.extend(batch)
            if len(batch) < s.NAVATEL_PAGE_SIZE:
                return items
            page += 1

    # --- resource fetchers (normalized to canonical field names) ----------

    def get_contacts(self) -> list[dict]:
        rows = self._get_all_pages(self.settings.endpoints["contacts"])
        return _apply_aliases(rows, self.settings.field_aliases["contacts"])

    def get_orders(self) -> list[dict]:
        rows = self._get_all_pages(self.settings.endpoints["orders"])
        return _apply_aliases(rows, self.settings.field_aliases["orders"])

    def get_call_logs(self) -> list[dict]:
        rows = self._get_all_pages(self.settings.endpoints["calls"])
        return _apply_aliases(rows, self.settings.field_aliases["calls"])

    def get_sms_logs(self) -> list[dict]:
        rows = self._get_all_pages(self.settings.endpoints["sms"])
        return _apply_aliases(rows, self.settings.field_aliases["sms"])

    # --- write-back --------------------------------------------------------

    def update_contact_field(self, contact_id: str, field_name: str, value: Any) -> None:
        """Pushes the latest segment/persona onto the Navatel contact record
        (custom fields bamipet_rfm_segment / bamipet_persona_guess). PATCH on
        the contact resource is the assumed verb — confirm against Swagger
        before first live write-back, and only enable via ENABLE_WRITEBACK."""
        path = f"{self.settings.endpoints['contacts'].rstrip('/')}/{contact_id}"
        self._request("PATCH", path, json={field_name: value})

    def close(self) -> None:
        self._client.close()


def get_navatel_client(settings: Settings | None = None) -> NavatelClientProtocol:
    """Factory the sync job uses. NAVATEL_MODE=mock (default) serves the
    deterministic demo dataset so the entire stack runs before real
    credentials exist; NAVATEL_MODE=live talks to the real gateway."""
    settings = settings or get_settings()
    if settings.NAVATEL_MODE == "live":
        return NavatelClient(settings)
    from sync.mock_navatel import MockNavatelClient
    return MockNavatelClient()
