# Bamipet RFM — Production Build Plan · نقشهٔ ساخت (Level 5 · Execution)

> **How to use this file.** `bamipet-rfm-system-spec.md` is the *architecture and UX spec* (what to build, why). This file is the *execution plan* — the concrete engineering decisions, gap list, API contracts, page-by-page UI spec, and phased build order needed to actually ship a production-grade, bilingual RFM dashboard. Written so **Fable 5 can build directly from this document** with minimal re-derivation.
>
> Scope confirmed by stakeholder (2026-07-08): **full production software** — scoring engine + sync job + warehouse + backend API + bilingual (FA/EN) dashboard + write-back + auth, "best UI/UX, fully production ready and usable." Not a prototype.

---

## Part 0 — Repo Audit: What Exists vs. What's Missing

### Already in the repo (reuse, don't rebuild)
| File | State |
|---|---|
| `bamipet-rfm-system-spec.md` | Complete architecture + bilingual UX spec — authoritative for design decisions |
| `bamipet-foundation.md`, `bamipet-personas.md`, `bamipet-messaging-architecture.md`, `bamipet-operating-team.md` | Brand strategy — governs segment→persona→pillar mapping and tone |
| `bamipet-visual-guidelines.md` | Color/type/spacing tokens |
| `bamipet-1-foundation.html`, `bamipet-2-personas.html`, etc. | **Working, brand-validated CSS** (see Part 5 — lift these tokens directly) |
| `config.py` | Env vars, endpoint placeholders, RFM window — needs real values, not structure |
| `rfm_engine.py` | R/F/M/E quintile scoring + 9-segment labeling — solid, keep as-is with minor hardening (Part 4) |
| `persona_mapper.py` | Segment → persona guess → pillar → journey stage — solid, keep as-is |
| `main.py` | Batch-script pipeline entry point — becomes the model for the scheduled sync **job**, not the whole app |
| `Pinar V2 @fontineh.zip` | Farsi font family (weights: Light–Black, plus Farsi-digit variants) |

### Missing — must be built (this is most of the work)
1. **`navatel_client.py` — does not exist.** `main.py` and `README.md` both import/reference it; it was never committed. This is the actual REST adapter to Navatel and is the single most important missing piece.
2. No database layer (no models, no migrations, no `rfm_snapshots` table implementation — only a SQL sketch in the spec).
3. No backend API (FastAPI layer in front of Postgres — spec calls for it, nothing built).
4. No frontend/dashboard at all.
5. No scheduler wiring (nightly cron/job runner).
6. No auth.
7. No tests, no Docker/deployment packaging.

### Discrepancy to flag (not blocking, but must be resolved before final polish)
- `bamipet-visual-guidelines.md` locks **Vazirmatn** as the Farsi typeface ("never swap these roles"), and the reference HTML files load Vazirmatn from Google Fonts.
- The font asset actually committed to the repo is **Pinar**, a different Farsi family, with no Vazirmatn files present.
- **Default for the build:** use **Vazirmatn** (self-hosted, not CDN — see Part 5) since it's what the locked brand doc and every existing HTML reference specify. Bundle Pinar as a selectable alternate only if the team confirms a brand update; do not let it silently replace Vazirmatn. Flag this explicitly to the user before Fable 5 finalizes typography — one Slack-style confirmation, not a blocker to starting the build.

---

## Part 1 — Tech Stack (concrete decisions, not options)

| Layer | Choice | Why |
|---|---|---|
| Sync + scoring | Python 3.11+, `pandas`, `httpx` (swap for `requests`) | Already the language of `rfm_engine.py`/`persona_mapper.py` — extend, don't rewrite |
| Backend API | FastAPI + Pydantic v2 | Matches spec's "FastAPI or similar"; async, typed, OpenAPI docs for free (nice parity with Navatel's own API-first approach) |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Standard, typed, migration history for the warehouse schema |
| Database | PostgreSQL 15+ | Matches spec exactly |
| Scheduler | APScheduler running inside a small `worker` process (in-repo, in Docker Compose) | Simpler ops than external cron for a single small instance; falls back to OS cron trivially if preferred later |
| Auth | JWT (short-lived access + refresh) via `python-jose` + `passlib[bcrypt]`, individual team logins | Spec allows "even a shared password," but "production ready and usable" implies real accounts with roles (`admin`, `viewer`) — cheap to do right from day one |
| Frontend | React 18 + TypeScript + Vite | Fast dev loop, best ecosystem fit for bilingual RTL/LTR + charting |
| Styling | Tailwind CSS, configured with Bamipet's tokens as the theme (not default Tailwind palette) | Matches design-token table in `bamipet-visual-guidelines.md` 1:1 |
| Data fetching / tables | TanStack Query + TanStack Table | Filtering/sorting/pagination for the Customer Table view without hand-rolling |
| Charts | Recharts | Donut/bar/line, easy RTL-aware axis control (needed per spec §4.2 exception) |
| i18n | `react-i18next`, `dir` attribute driven off active language | FA-first default per spec §4.8 |
| Dates | `jalaali-js` for Gregorian⇄Jalali display conversion | Storage stays ISO 8601 always (spec §4.5) |
| Packaging | Docker Compose: `postgres`, `api`, `worker`, `web` (+ `Caddy` or `nginx` reverse proxy in prod) | One-command local run, portable to any cloud host |

---

## Part 2 — Data Model

Extends the spec's single-table sketch with what a real running system needs: an audit trail and a login table.

```sql
-- from spec, kept as the core fact table
CREATE TABLE rfm_snapshots (
    id                  BIGSERIAL PRIMARY KEY,
    contact_id          TEXT NOT NULL,
    run_date            DATE NOT NULL,
    recency_days        INT,
    order_count         INT,
    total_amount        NUMERIC,
    touch_count         INT,
    r_score             SMALLINT,
    f_score             SMALLINT,
    m_score             SMALLINT,
    e_score             SMALLINT,
    segment             TEXT,
    persona_guess       TEXT,
    persona_confidence  TEXT,   -- 'confirmed' | 'inferred'
    lead_pillar         TEXT,
    journey_stage       TEXT,
    UNIQUE (contact_id, run_date)
);
CREATE INDEX idx_rfm_snapshots_run_date ON rfm_snapshots (run_date);
CREATE INDEX idx_rfm_snapshots_contact  ON rfm_snapshots (contact_id, run_date DESC);

-- denormalized contact info cache, refreshed each sync run, so dashboard
-- never calls Navatel live for names/phone numbers
CREATE TABLE contacts_cache (
    contact_id      TEXT PRIMARY KEY,
    display_name    TEXT,
    phone           TEXT,
    species         TEXT,        -- 'cat' | 'dog' | NULL, once confirmed in Navatel schema
    channel         TEXT,        -- 'online' | 'in_store' | NULL, if resolvable
    updated_at      TIMESTAMPTZ NOT NULL
);

-- audit log of every sync run
CREATE TABLE sync_runs (
    id              BIGSERIAL PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    status          TEXT NOT NULL,   -- 'running' | 'success' | 'failed'
    contacts_count  INT,
    orders_count    INT,
    calls_count     INT,
    sms_count       INT,
    error_message   TEXT
);

-- team accounts
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'viewer',  -- 'admin' | 'viewer'
    language_pref   TEXT NOT NULL DEFAULT 'fa',
    numerals_pref   TEXT NOT NULL DEFAULT 'western',  -- 'western' | 'persian'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Part 3 — Navatel Integration Plan

### 3.1 Build `navatel_client.py` (the missing file)
Responsibilities:
- `get_contacts()`, `get_orders()`, `get_call_logs()`, `get_sms_logs()` — paginated GET loops using `config.ENDPOINTS`, `PAGE_PARAM`/`PAGE_SIZE_PARAM`, Bearer auth header from `NAVATEL_API_TOKEN`.
- `update_contact_field(contact_id, field_name, value)` — write-back, currently unused/commented out in `main.py`.
- Retry with exponential backoff on 429/5xx; respect any `Retry-After` header.
- Raise a typed `NavatelAPIError` on non-2xx so the sync job can log a clean failure into `sync_runs` instead of crashing silently.
- **Field-mapping is config-driven, not hardcoded.** Add a `FIELD_ALIASES` dict to `config.py` (e.g. `{"orders": {"id": "faktor_id", "amount": "mablagh_kol", "created_at": "tarikh_sabt"}}`) that `navatel_client.py` applies when normalizing raw API rows into the shape `rfm_engine.build_customer_table()` already expects. This means remapping real Navatel field names later is a config edit, not a code change.

### 3.2 Blocking dependency — cannot be resolved by research alone
Navatel's Swagger/OpenAPI docs are **behind login** at `cp.navatel.ir` (confirmed — no public API documentation exists for navatel.ir; web search returned nothing beyond marketing pages). This was already flagged correctly in the existing `README.md` and spec §Part 6. **Action required from the user before the sync job can run against real data:**
1. Log into `cp.navatel.ir` → API/webservice section, generate a Bearer token.
2. Copy the `servers` base URL from the Swagger doc → `NAVATEL_BASE_URL`.
3. Copy the 4 real endpoint paths (contacts, orders/invoices, calls, SMS) → `config.ENDPOINTS`.
4. Copy real field names from each endpoint's response schema → `config.FIELD_ALIASES`.
5. Confirm whether `bamipet_rfm_segment` / `bamipet_persona_guess` custom fields exist on a contact, or create them, before enabling write-back.
6. Confirm whether in-store sales flow into the same order/invoice endpoint or live in a separate POS (per spec's open question — determines whether this system sees all revenue or only the online slice).

**Fable 5 should not block the whole build on this.** Build and test the entire pipeline (client → engine → warehouse → API → dashboard) against a **fixture/mock Navatel response set** (recorded JSON samples shaped like the field-name placeholders already in `rfm_engine.py`) so the system is fully demoable and testable before real credentials exist. Swapping in the real base URL/paths/field aliases at the end should require zero code changes — only `config.py` edits.

---

## Part 4 — Scoring Engine Hardening

`rfm_engine.py` and `persona_mapper.py` are logically sound; production hardening needed:
- Move the 9 segment labels into a single lookup used by **both** the Python layer and the frontend, with the Farsi display label attached (not yet defined anywhere — table below is new):

| Internal segment (code) | Farsi label (dashboard) | Dashboard color token |
|---|---|---|
| Champions | قهرمانان | Calm Green `#2F8F6B` |
| Loyal Customers | مشتریانِ وفادار | Calm Green `#2F8F6B` |
| New Customers | مشتریانِ جدید | Bamipet Blue `#1C48C1` |
| Promising | امیدبخش | Blue Soft `#2E5BE0` |
| Needs Attention | نیازمندِ توجه | Honey Amber `#B77E33` |
| At Risk | در معرضِ ریزش | Terracotta `#C1543A` *(new — see spec §4.7)* |
| Can't Lose Them | نبایدشان را از دست داد | Terracotta `#C1543A` |
| Hibernating / Lost | به‌خواب‌رفته | Ink 40% opacity (neutral/muted) |
| About To Sleep | در آستانهٔ رکود | Honey Amber `#B77E33` |

- Add `warehouse.py`: takes `score_rfm()`'s output DataFrame and upserts into `rfm_snapshots` (one row per `contact_id, run_date`, matching the `UNIQUE` constraint) — this is the piece that currently doesn't exist between "compute scores" and "print to console."
- Unit tests with small fixture DataFrames covering: zero-order contacts, single-contact dataset (qcut fallback path), a contact with `species='dog'` (confirmed persona path).

---

## Part 5 — Frontend Design System (lift, don't reinvent)

The existing HTML brand documents (`bamipet-1-foundation.html` et al.) already contain a **validated, working CSS implementation** of the brand — use it as the literal source for the dashboard's Tailwind theme rather than re-deriving from the token tables:

```css
:root {
  --cobalt: #1C48C1;      /* primary */
  --cobalt-deep: #123086;
  --cobalt-soft: #2E5BE0;
  --ink: #1A1E2E;          /* text */
  --cream: #FAF9F6;        /* base background — never pure white */
  --cream-2: #F4F2EC;
  --amber: #B77E33;        /* reserved: trust/attention */
  --green: #2F8F6B;        /* affirmative */
  --terracotta: #C1543A;   /* new: at-risk/danger, pending team sign-off */
}
```
- Font stack: Vazirmatn (FA, self-hosted `.woff2`, weights 300–800) + Inter (EN + all numerals/dates/IDs), per Part 0's flagged decision.
- Spacing/radius: reuse `space-xs/sm/md/lg/xl` and `radius-sm/md/full` tokens verbatim from `bamipet-visual-guidelines.md` as Tailwind theme extensions.
- Background is always `--cream`, never `#fff` — matches the "never pure white" rule used consistently across every brand doc.
- Cards: `radius-md` (8px), soft shadow (`0 1px 2px rgba(18,48,134,.05), 0 40px 80px -40px rgba(18,48,134,.22)` — lifted directly from `bamipet-1-foundation.html`), 1px `--line` border.

### 5.1 RTL/LTR mechanics
- `<html dir="rtl" lang="fa">` default; toggling language flips `dir` and swaps the whole layout (sidebar left↔right, table column order mirrors — not just text-align), per spec §4.2.
- Chart time-axes stay left→right in both modes (spec's explicit exception).
- Mixed-content table cells (Latin customer names inside RTL rows) get `dir="auto"`.

### 5.2 Numerals & dates
- Default Western numerals even in FA mode; per-user toggle to Persian numerals (stored in `users.numerals_pref`).
- Dates stored ISO 8601; displayed Jalali in FA mode / Gregorian in EN mode via `jalaali-js`, never changing storage format.

---

## Part 6 — Backend API Contract

All routes under `/api/v1`, JWT-protected except `/auth/login`.

| Method & Path | Purpose | Notes |
|---|---|---|
| `POST /auth/login` | Issue JWT | username + password |
| `GET /me` | Current user + prefs | language, numerals, role |
| `GET /segments/overview` | Counts per segment, latest `run_date` | powers donut/bar chart |
| `GET /personas/overview` | Counts per persona guess | powers persona distribution view |
| `GET /contacts` | Paginated, filterable, sortable contact list | query params: `segment`, `persona`, `journey_stage`, `search`, `sort`, `page`, `page_size` |
| `GET /contacts/{contact_id}` | Full snapshot history for one contact | powers drill-down + trend line |
| `GET /trends/segment-migration` | Segment counts by `run_date`, or transition matrix between two dates | `from`, `to` query params |
| `GET /sync-runs` | Recent sync job history | admin view |
| `POST /sync-runs/trigger` | Manually trigger a sync (admin only) | enqueues the worker job |
| `GET /export/contacts.csv` | CSV export of filtered contact list | same filters as `/contacts` |

---

## Part 7 — Dashboard Pages (route-by-route build spec)

1. **Login** — brand-blue mark, cream background, single form, no clutter (matches "calm" visual principle).
2. **Overview (`/`)** — KPI tiles (total contacts, Champions count, At Risk count, last sync timestamp + status), segment donut chart, persona distribution bar chart. Farsi-first, EN toggle top-right (mirrors to top-left in RTL... actually stays a fixed corner control per convention — confirm placement doesn't fight the RTL mirror rule).
3. **Customers (`/customers`)** — filterable/sortable table (segment, persona, journey stage dropdowns; free-text search), column order mirrors per language, pagination, CSV export button, click-through to drill-down.
4. **Customer drill-down (`/customers/:id`)** — contact info card, full R/F/M/E history table, segment-over-time line/step chart, list of recent orders/calls/SMS (from `contacts_cache` + snapshot history).
5. **Trends (`/trends`)** — segment migration view (e.g., stacked bar or flow showing how many moved Champions→At Risk etc. month over month), date-range picker (Jalali-aware).
6. **Sync & Admin (`/admin/sync`, admin role only)** — last N sync runs with status/counts/errors, manual "Run sync now" button, read-only view of active `FIELD_ALIASES`/`ENDPOINTS` config for debugging (never expose the token itself).
7. **Settings (`/settings`)** — language toggle (FA default), numerals toggle, calendar display is tied to language automatically per spec.

Every page: cream background, brand-blue primary actions, generous spacing (`space-lg`/`space-xl` between sections) — "calm, uncluttered" per the visual guideline's governing principle, not a dense admin-panel look despite being an internal tool.

---

## Part 8 — Auth & Roles

- `admin`: everything a `viewer` has, plus trigger manual sync, view sync/admin page, (later) trigger write-back.
- `viewer`: everything else (all dashboard views, export).
- Seed one admin account on first deploy via an env-var-driven bootstrap script (`create_admin.py` or a migration data seed) — never hardcode a password in source.

---

## Part 9 — Build Phases (execution order for Fable 5)

| Phase | Deliverable | Can start before real Navatel creds? |
|---|---|---|
| **1** | `navatel_client.py` built against fixture/mock JSON; `config.FIELD_ALIASES` mechanism in place | Yes |
| **2** | Postgres schema + Alembic migrations; `warehouse.py` upsert logic; sync job wired end-to-end on mock data | Yes |
| **3** | FastAPI backend implementing the Part 6 contract, reading from Postgres | Yes |
| **4** | React dashboard: Overview + Customers + drill-down pages, bilingual, branded per Part 5 | Yes |
| **5** | Auth (JWT, roles), Trends page, Admin/Sync page | Yes |
| **6** | Docker Compose packaging (all 4 services), seed/demo data script, README rewrite for the full stack | Yes |
| **7** | Unit + integration tests (engine, client against fixtures, API contract tests), basic Playwright smoke test of the dashboard | Yes |
| **8** | **Swap in real Navatel base URL / endpoints / field aliases**, validate against a small real data slice, enable write-back | **Blocked on user pulling Swagger docs from `cp.navatel.ir`** (Part 3.2) |
| **9** | Production hardening: rate-limit handling verified against real API, error alerting on failed sync runs, backups for Postgres, hosting deploy | After Phase 8 |

Phases 1–7 are fully buildable and demoable right now with mock data. Phase 8 is the only hard external dependency.

---

## Part 10 — Open Decisions Needing a Quick Answer (not full blockers)

Carried over from `bamipet-rfm-system-spec.md` Part 6, plus new ones from this audit:

- [ ] **Font: Vazirmatn vs. Pinar** (Part 0) — default is Vazirmatn per locked visual guidelines; confirm if Pinar should replace it.
- [ ] **Auth strength** — this plan defaults to individual logins + JWT instead of the spec's "shared password is fine" — confirm that's acceptable scope.
- [ ] Navatel real endpoint paths, base URL, field names (Part 3.2) — needs `cp.navatel.ir` panel access.
- [ ] Whether in-store sales flow into Navatel's order/invoice records or a separate POS.
- [ ] Whether `species` (cat/dog) exists as a real field in Navatel's schema.
- [ ] Default dashboard language on load — Farsi-first proposed, needs sign-off.
- [ ] Adopt the proposed terracotta `#C1543A` "at risk" color, or pick an existing token instead.
- [ ] Hosting target (which cloud provider / self-hosted) for the final Docker Compose stack.
- [ ] Confirm/create the `bamipet_rfm_segment` / `bamipet_persona_guess` custom fields in Navatel before enabling write-back.

None of these block Phases 1–7. They should be resolved before Phase 8–9.

---

## Part 11 — Proposed Repo Structure

```
bamipet-rfm-navatel/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app entry
│   │   ├── api/                   # route modules per Part 6
│   │   ├── models/                # SQLAlchemy models (Part 2)
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── auth/
│   │   └── config.py
│   ├── sync/
│   │   ├── navatel_client.py      # Part 3.1 — the missing piece
│   │   ├── rfm_engine.py          # existing, hardened per Part 4
│   │   ├── persona_mapper.py      # existing
│   │   ├── warehouse.py           # new — upsert into rfm_snapshots
│   │   └── job.py                 # scheduler entry (was main.py)
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                 # Part 7 routes
│   │   ├── components/
│   │   ├── i18n/                  # fa.json, en.json
│   │   ├── theme/                 # Tailwind config w/ brand tokens (Part 5)
│   │   └── assets/fonts/          # Vazirmatn + Inter .woff2
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

---

*Bamipet RFM — Production Build Plan · Level 5 · v1.0 · execution-ready for Fable 5.*
