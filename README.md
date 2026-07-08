# Bamipet × Navatel — RFM+Engagement System · سامانهٔ تحلیل و تقسیم‌بندی مشتریان

A complete, production-ready customer analytics product for Bamipet:
it pulls contacts, orders/invoices, call logs and SMS logs from
**Navatel's unified CRM**, scores every contact on
**Recency / Frequency / Monetary / Engagement** (RFM+E), maps each one to a
Bamipet persona (نگار / سارا / کیان / امیر), stores an append-only history in
Postgres, and serves a **bilingual (فارسی-first, RTL/LTR) branded dashboard**
where the team can answer "who's at risk this week?" without touching code.

Built from [`bamipet-rfm-system-spec.md`](./bamipet-rfm-system-spec.md)
(architecture & UX spec) via [`bamipet-rfm-build-plan.md`](./bamipet-rfm-build-plan.md)
(execution plan). Brand system per [`bamipet-visual-guidelines.md`](./bamipet-visual-guidelines.md).

---

## What's in the box

```
┌─ NAVATEL API Gateway (или mock) ──> worker: nightly sync + RFM+E scoring ─┐
│                                                                            ▼
│   frontend/  React+TS dashboard  <──  backend/app  FastAPI  <──  Postgres warehouse
│   (nginx, bilingual FA/EN)            (JWT auth, REST)          (snapshot history)
└─ optional write-back of segment/persona onto Navatel contacts ────────────┘
```

| Piece | Where | Notes |
|---|---|---|
| Sync + scoring engine | `backend/sync/` | `navatel_client.py` (live) / `mock_navatel.py` (demo), `rfm_engine.py`, `persona_mapper.py`, `warehouse.py`, `job.py`, `worker.py` (APScheduler, nightly 02:30 Tehran) |
| Warehouse | Postgres | `rfm_snapshots` (append-only per contact per run), `contacts_cache`, `sync_runs`, `users` — migrations in `backend/alembic/` |
| API | `backend/app/` | JWT auth + roles (admin/viewer), segments/personas overview, filterable customer table, drill-down history, segment-migration trends, CSV export, sync trigger, user management. Docs at `/api/docs` |
| Dashboard | `frontend/` | Farsi-first RTL with full English/LTR mirror, Jalali/Gregorian dual calendar, Persian-numeral toggle, Vazirmatn+Inter (self-hosted), brand tokens throughout |
| Tests | `backend/tests/` | scoring direction & tie-fairness, persona rules, sync idempotency, full API contract (18 tests) |

## Quick start (Docker — recommended)

```bash
cp .env.example .env        # edit: POSTGRES_PASSWORD, SECRET_KEY, admin bootstrap
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.create_admin
docker compose exec api python -m scripts.seed_demo    # optional: 7 months of demo history
```

Open **http://localhost:8080** and sign in with the bootstrap admin account.
The system starts in **mock mode**: a deterministic, realistic demo dataset
(420 contacts, Persian names, Toman amounts, all segments/personas populated)
so the entire product is usable before any Navatel credential exists.

## Going live — the only remaining input

Navatel's OpenAPI/Swagger docs are behind login at `cp.navatel.ir`
(panel → API/webservice). Five values from there complete the system —
**all config, zero code changes**:

1. `NAVATEL_BASE_URL` — the Swagger `servers` URL.
2. `NAVATEL_API_TOKEN` — Bearer token generated in the panel.
3. The four endpoint paths → `NAVATEL_ENDPOINT_*`.
4. Real field names → `NAVATEL_FIELD_ALIASES` (JSON, canonical → real; see `.env.example`).
5. Set `NAVATEL_MODE=live`, restart, and run one sync from the dashboard's
   Sync page (admin) to validate against a real data slice.

Then, optionally: create the custom fields `bamipet_rfm_segment` /
`bamipet_persona_guess` on Navatel contacts and set `ENABLE_WRITEBACK=true`
so segments are visible inside Navatel itself.

**Also confirm** (spec Part 6): whether in-store sales flow into Navatel's
invoices (else the system sees only the online slice), and whether a
`species` (cat/dog) field exists (activates the *confirmed* کیان mapping —
until then it's behavior-inferred only).

## Local development

```bash
# backend (Python 3.11+, needs a local Postgres or SQLite URL)
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://bamipet:bamipet_dev@localhost:5432/bamipet_rfm
.venv/bin/alembic upgrade head
BOOTSTRAP_ADMIN_USERNAME=admin BOOTSTRAP_ADMIN_PASSWORD=... .venv/bin/python -m scripts.create_admin
.venv/bin/python -m scripts.seed_demo
.venv/bin/uvicorn app.main:app --reload          # API on :8000
.venv/bin/python -m pytest tests/ -q             # test suite

# frontend (Node 20+)
cd frontend && npm install && npm run dev        # dashboard on :5173, proxies /api → :8000
```

## Operations

- **Nightly sync** runs in the `worker` container (02:30 Asia/Tehran by
  default — `SYNC_CRON_HOUR`/`SYNC_CRON_MINUTE`). One-off run:
  `docker compose exec worker python -m sync.worker --once`.
- Every run — scheduled, manual, or seed — is audited in `sync_runs` and
  visible on the dashboard's Sync page, including failures with error text.
- Re-running a sync on the same date **replaces** that date's snapshot
  (idempotent); history for other dates is never touched.
- **Backups**: the warehouse is one small Postgres volume (`pgdata`) —
  standard `pg_dump` on a cron covers it.
- **Accounts**: admins manage users on the Sync page. A forgotten admin
  password is recoverable server-side via `scripts/create_admin.py`.

## ⚠️ Brand-safety note — read before segments touch any campaign

This system produces analytics, not copy. Whatever channel a segment feeds —
an SMS blast through Navatel's messaging panel, an ad audience, a DM script —
the actual words must pass `bamipet-3-voice-message-copy.md`'s Pre-Publish
Checklist. The segment most at risk of misuse is **At Risk / Hibernating**:
the standard e-commerce move is a discount SMS, and that directly violates
Bamipet's Non-Negotiable Rules (no money words, ever). A win-back message is
pillar ۴ reassurance — «دلمون برای همراهت تنگ شده، حالش چطوره؟» — never a
coupon code. The dashboard's suggested lead pillar for these segments says
`(بدونِ تخفیف)` for exactly this reason.

## Repository map

| Path | What |
|---|---|
| `backend/` | FastAPI app, sync engine, migrations, tests, scripts |
| `frontend/` | React dashboard (Vite + TS + Tailwind, brand tokens) |
| `docker-compose.yml`, `.env.example` | Full-stack deployment |
| `bamipet-rfm-system-spec.md` | Level-4 architecture & bilingual UX spec (source of truth) |
| `bamipet-rfm-build-plan.md` | Execution plan this build followed |
| `bamipet-*.md` / `.html` | Brand book: foundation, personas, voice, visual guidelines, ops team |
| `Pinar V2 @fontineh.zip` | Alternate Farsi typeface (unused — Vazirmatn is the locked brand face; see build plan Part 0) |
