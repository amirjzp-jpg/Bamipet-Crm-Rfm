"""
Central settings for the Bamipet RFM system — API, sync worker, and scripts
all read from here. Every value can be overridden with an environment
variable of the same name (see .env.example at the repo root).

The Navatel section is the ONLY part that needs real values before going
live: set NAVATEL_MODE=live plus the base URL / token / endpoint paths /
field aliases from the Swagger docs in the cp.navatel.ir panel.
"""
from __future__ import annotations

import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# Default field aliases: how Navatel's raw JSON keys map onto the canonical
# names the RFM engine expects (id / contact_id / amount / created_at ...).
# Identity mapping by default; override with the real Swagger field names
# via the NAVATEL_FIELD_ALIASES env var (JSON) once known — no code change.
DEFAULT_FIELD_ALIASES: dict[str, dict[str, str]] = {
    "contacts": {"id": "id", "name": "name", "phone": "phone", "species": "species"},
    "orders": {"id": "id", "contact_id": "contact_id", "amount": "amount", "created_at": "created_at"},
    "calls": {"id": "id", "contact_id": "contact_id", "created_at": "created_at"},
    "sms": {"id": "id", "contact_id": "contact_id", "created_at": "created_at"},
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg://bamipet:bamipet_dev@localhost:5432/bamipet_rfm"

    # --- Auth ---
    SECRET_KEY: str = "change-me-in-production"  # MUST be overridden in prod (.env)
    ACCESS_TOKEN_MINUTES: int = 720          # 12h — internal tool, working-day session
    REFRESH_TOKEN_DAYS: int = 30
    BOOTSTRAP_ADMIN_USERNAME: str = ""       # used once by scripts/create_admin.py
    BOOTSTRAP_ADMIN_PASSWORD: str = ""

    # --- Navatel ---
    NAVATEL_MODE: str = "mock"               # "mock" until real creds exist, then "live"
    NAVATEL_BASE_URL: str = "https://api.navatel.ir"  # from Swagger "servers" block
    NAVATEL_API_TOKEN: str = ""              # Bearer token from panel > API/webservice
    # The four endpoint paths, from the Swagger docs (placeholders until confirmed):
    NAVATEL_ENDPOINT_CONTACTS: str = "/crm/v1/contacts"
    NAVATEL_ENDPOINT_ORDERS: str = "/crm/v1/invoices"
    NAVATEL_ENDPOINT_CALLS: str = "/call/v1/logs"
    NAVATEL_ENDPOINT_SMS: str = "/messaging/v1/logs"
    NAVATEL_PAGE_PARAM: str = "page"
    NAVATEL_PAGE_SIZE_PARAM: str = "page_size"
    NAVATEL_PAGE_SIZE: int = 200
    NAVATEL_FIELD_ALIASES: str = ""          # JSON override of DEFAULT_FIELD_ALIASES
    NAVATEL_TIMEOUT_SECONDS: float = 30.0
    NAVATEL_MAX_RETRIES: int = 4

    # --- RFM engine ---
    LOOKBACK_DAYS: int = 365                 # window for F/M/E counts
    SEGMENT_FIELD_NAME: str = "bamipet_rfm_segment"    # write-back custom field
    PERSONA_FIELD_NAME: str = "bamipet_persona_guess"  # write-back custom field
    ENABLE_WRITEBACK: bool = False           # keep off until custom fields confirmed in Navatel

    # --- Scheduler (worker process) ---
    SYNC_CRON_HOUR: int = 2                  # nightly at 02:00 server time
    SYNC_CRON_MINUTE: int = 30

    # --- CORS (dev convenience; nginx proxies same-origin in prod) ---
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def endpoints(self) -> dict[str, str]:
        return {
            "contacts": self.NAVATEL_ENDPOINT_CONTACTS,
            "orders": self.NAVATEL_ENDPOINT_ORDERS,
            "calls": self.NAVATEL_ENDPOINT_CALLS,
            "sms": self.NAVATEL_ENDPOINT_SMS,
        }

    @property
    def field_aliases(self) -> dict[str, dict[str, str]]:
        if not self.NAVATEL_FIELD_ALIASES:
            return DEFAULT_FIELD_ALIASES
        merged = {k: dict(v) for k, v in DEFAULT_FIELD_ALIASES.items()}
        for resource, mapping in json.loads(self.NAVATEL_FIELD_ALIASES).items():
            merged.setdefault(resource, {}).update(mapping)
        return merged

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
