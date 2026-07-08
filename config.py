"""
Bamipet x Navatel -- RFM+Engagement Engine Configuration

Navatel is API-First (confirmed): separate microservices behind one API
Gateway for Call Services, Messaging Services, and CRM Services (which also
handles invoices/orders per their own product copy). Auth is a Bearer token
issued from the panel. Exact paths are in their Swagger/OpenAPI docs at
cp.navatel.ir (behind login) -- fill in ENDPOINTS below once you have that
open. Everything downstream (rfm_engine.py, persona_mapper.py, main.py)
is already wired to these four calls and does not need to change.
"""
import os

NAVATEL_BASE_URL = os.getenv("NAVATEL_BASE_URL", "https://api.navatel.ir")  # TODO confirm exact gateway host from Swagger "servers" block
NAVATEL_API_TOKEN = os.getenv("NAVATEL_API_TOKEN", "")  # Bearer token, generated in panel > API/webservice section

# TODO: replace these four paths with the real ones from the Swagger docs.
# Given the microservice split described in their architecture doc, expect
# these to live on genuinely different service paths, not one shared endpoint.
ENDPOINTS = {
    "contacts": "/crm/v1/contacts",     # CRM service -- customer/contact records
    "orders":   "/crm/v1/invoices",     # CRM service -- orders/invoices (they explicitly mention فاکتور + انبار)
    "calls":    "/call/v1/logs",        # Call service -- call logs per contact
    "sms":      "/messaging/v1/logs",   # Messaging service -- SMS logs per contact
}

# Common pagination param names to check against the Swagger docs (adjust in navatel_client.py if different)
PAGE_PARAM = "page"
PAGE_SIZE_PARAM = "page_size"
PAGE_SIZE = 200

# --- RFM+E settings ---
LOOKBACK_DAYS = 365          # window for Frequency/Monetary/Engagement counts
RECENCY_REFERENCE = None     # None = use "today"; or set a fixed datetime for reproducible reports

# Where the computed segment gets written back onto each contact in Navatel CRM
# (confirm this is a valid custom-field name in your CRM schema, or create one)
SEGMENT_FIELD_NAME = "bamipet_rfm_segment"
PERSONA_FIELD_NAME = "bamipet_persona_guess"
