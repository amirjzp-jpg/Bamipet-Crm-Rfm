# Bamipet — RFM+Engagement System · سامانهٔ تحلیل و تقسیم‌بندی مشتریان (Level 4 · Ops Infrastructure)

> **How to use this file.** This is the project-level spec for the customer segmentation system built on top of Navatel — the layer that turns raw CRM/call/SMS/order data into segments, persona guesses, and eventually a bilingual dashboard the team actually looks at. Pairs with `bamipet-operating-team.md` (roles/pipeline) and the code package `bamipet-rfm-navatel/`. Written in English (technical spec); the **product itself must be bilingual** — see Part 4.

---

## Part 1 — Objective · هدف

### The business problem
Bamipet has customer data spread across Navatel's unified CRM (contacts, orders/invoices, call logs, SMS logs) but no systematic way to answer:
- Who are our best customers, and are we treating them like it?
- Who's slipping away, and can we catch it before they're gone?
- Who's a new, anxious first-timer (نگار) generating lots of calls/questions but hasn't bought much yet — and would churn without follow-up?
- Which customers behave like سارا, کیان, or امیر, so Marketing & Copywriter roles know which pillar/tone to lead with (per `bamipet-messaging-architecture.md`), instead of guessing?

**Right now this is invisible.** It lives implicitly in individual staff members' memory of "regular customers," not in a system anyone can query, filter, or act on consistently.

### What "done" looks like
1. Every contact in Navatel has a current **RFM+Engagement segment** and a **persona guess**, recomputed on a schedule (not a one-off).
2. Someone on the team (Persian-speaking, non-technical) can open a dashboard and answer "who's at risk this week?" or "how many نگار-type new customers do we have?" without touching code.
3. Segments are usable downstream — by Marketing & Growth for ad audiences, by Community & Comms for prioritizing DM follow-up, by the Copywriter role for picking the right pillar — **without ever violating the Non-Negotiable Rules** (no money words, no discount-driven win-back).
4. The system is auditable: every score is explainable from raw order/call/SMS data, not a black box.

### Non-goals (for this phase)
- This is **not** a full customer data platform or a replacement for Navatel — Navatel remains the system of record. This system reads from it, computes on top, and writes a small number of fields back.
- This is **not** an automated messaging system. It produces segments and recommendations; a human (Comms/Copywriter/Marketing role) still writes and sends anything customer-facing.
- Discount/coupon logic is explicitly **out of scope** — it would conflict with brand rules; see Part 3.

---

## Part 2 — What We're Building · چه می‌سازیم

Four layers, each doing one job:

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. NAVATEL (system of record)                                       │
│     CRM service · Call service · Messaging service — behind one       │
│     API Gateway, Bearer-token auth, OpenAPI/Swagger-documented.       │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │  scheduled pull (nightly)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. SYNC + SCORING JOB  (bamipet-rfm-navatel/ package)                │
│     navatel_client.py → rfm_engine.py → persona_mapper.py              │
│     Computes R/F/M/E scores, segment label, persona guess.             │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │  writes snapshot
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. WAREHOUSE  (small Postgres instance)                              │
│     Stores every historical snapshot — not just "latest" — so the     │
│     dashboard can show trend/movement between segments over time.     │
└───────────────────────────────┬───────────────────────────────────────┘
                     ┌───────────┴────────────┐
                     ▼                        ▼
        ┌─────────────────────┐   ┌─────────────────────────────┐
        │ 4a. WRITE-BACK       │   │ 4b. DASHBOARD (bilingual)    │
        │ Segment + persona    │   │ Read-only views for the team │
        │ tag pushed onto the  │   │ — see Part 4 for full UX/UI  │
        │ Navatel contact      │   │ spec.                        │
        └─────────────────────┘   └─────────────────────────────┘
```

**Why a warehouse, not just "read Navatel live every time":** Navatel is the operational system — hitting it repeatedly for every dashboard page load is unnecessary load and subject to whatever rate limits the API Gateway enforces. A snapshot-per-run history table also lets the dashboard answer "how has this customer's segment changed over the last 3 months?" — something Navatel's live API alone can't answer, since it only knows the current state, not the history of segment computations.

---

## Part 3 — Infrastructure · زیرساخت

### 3.1 Components

| Component | Technology (proposed) | Role |
|---|---|---|
| **Data source** | Navatel API Gateway (existing) | System of record — contacts, orders/invoices, calls, SMS |
| **Sync + scoring job** | Python (`bamipet-rfm-navatel/` package, already built) | Pulls, computes RFM+E, maps persona, writes back |
| **Scheduler** | Cron (simplest) or a managed scheduled function (cloud provider's cron/Lambda-equivalent) | Runs the job nightly (or the cadence the team wants) |
| **Warehouse** | PostgreSQL (small managed instance is enough at Bamipet's current scale) | Stores every snapshot: `customer_id, run_date, R, F, M, E, segment, persona_guess, raw_metrics` |
| **API layer** | Lightweight REST API (FastAPI or similar) in front of Postgres | Serves the dashboard; keeps DB credentials off the frontend |
| **Dashboard (frontend)** | Web app — React or plain HTML depending on team's build capacity | Bilingual EN/FA UI — full spec in Part 4 |
| **Auth for dashboard** | Simple team login (even a shared password or basic auth is fine at this scale — this is an internal tool, not customer-facing) | Restrict to internal team |
| **Write-back target** | Navatel CRM contact custom fields (`bamipet_rfm_segment`, `bamipet_persona_guess`) | So segment info is visible inside Navatel itself too, not only the new dashboard |

### 3.2 Data flow detail

1. **Nightly job** wakes up, calls `NavatelClient` for contacts, orders, calls, SMS (since last run).
2. `rfm_engine.build_customer_table()` joins them into one row per contact.
3. `rfm_engine.score_rfm()` computes R/F/M/E quintiles + segment label.
4. `persona_mapper.guess_persona()` adds persona guess + lead pillar + journey stage.
5. Job **inserts a new snapshot row per contact** into Postgres (append-only — never overwrite history).
6. Job calls `NavatelClient.update_contact_field()` to push the *latest* segment/persona onto the Navatel contact record.
7. Dashboard's API layer queries Postgres (latest snapshot for "current state" views, full history for trend views).

### 3.3 Minimal warehouse schema

```sql
CREATE TABLE rfm_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    contact_id      TEXT NOT NULL,
    run_date        DATE NOT NULL,
    recency_days    INT,
    order_count     INT,
    total_amount    NUMERIC,
    touch_count     INT,
    r_score         SMALLINT,
    f_score         SMALLINT,
    m_score         SMALLINT,
    e_score         SMALLINT,
    segment         TEXT,
    persona_guess   TEXT,
    persona_confidence TEXT,   -- 'confirmed' | 'inferred'
    lead_pillar     TEXT,
    journey_stage   TEXT,
    UNIQUE (contact_id, run_date)
);
```

This one table is enough to power every dashboard view in Part 4 — current snapshot (`WHERE run_date = latest`), and trend (`GROUP BY contact_id ORDER BY run_date`).

### 3.4 Environments & secrets

- `NAVATEL_API_TOKEN` and DB credentials live as environment variables / secrets manager — never hardcoded, never in the dashboard's frontend bundle.
- Recommend a staging pass against a small slice of real data before the first full nightly run, given the field-name assumptions flagged in the code package's README.

### 3.5 Cost/complexity note

At Bamipet's current scale (first-year markers: ~1,000 online invoices), this entire stack is intentionally small — a single small Postgres instance and a scheduled job comfortably handle this volume. Don't over-build; this is not a big-data problem yet.

---

## Part 4 — Bilingual UX/UI Specification (English + Farsi) · مشخصات رابط کاربری دوزبانه

The dashboard is an **internal tool**, but it should still carry Bamipet's visual identity (per `bamipet-visual-guidelines.md`) and work equally well for a Farsi-first team member and an English-reading stakeholder (e.g., an investor deck screenshot). Below is the full bilingual spec.

### 4.1 Core principle

**Farsi is not a translation layer bolted onto an English UI — it's a first-class layout mode.** The interface must mirror structurally (RTL), not just flip text strings inside an LTR frame. Numbers, dates, and charts need their own rules (below) — a UI that "works in Farsi" but still shows Latin numerals and LTR bar charts reads as broken, not bilingual.

### 4.2 Language & direction switching

| Element | English (LTR) | Farsi (RTL) |
|---|---|---|
| Text direction | `dir="ltr"` | `dir="rtl"` |
| Sidebar/nav position | Left | Right |
| Reading order of table columns | Left → right (e.g., Name, Segment, Last Order) | Right → left — **mirror the column order**, don't just right-align LTR columns |
| Icons with directional meaning (arrows, chevrons for "next," trend arrows) | Point right for "forward/next" | Flip horizontally — "next" points left |
| Charts (bar/line) | Standard left-to-right time axis | Time axis still generally reads left→right even in RTL UIs (a global convention audiences already expect) — **exception to full mirroring**, confirm with the team before flipping chart axes |

### 4.3 Typography

Directly inherited from `bamipet-visual-guidelines.md` — do not invent a separate type system for this internal tool:

| Role | Typeface |
|---|---|
| Farsi UI text, labels, segment names | **Vazirmatn** |
| English UI text, technical labels | **Inter** |
| Numerals, dates, IDs (both languages) | **Inter** — numerals stay in a consistent, tabular-figure font regardless of UI language, so tables of numbers align cleanly |

### 4.4 Numerals & number formatting

- **Default: Western Arabic numerals (0-9) even in the Farsi UI**, since this is an internal analytics tool where scannable alignment in tables matters more than full localization. Offer a **toggle** for Persian numerals (۰-۹) as a per-user preference, not a forced default — some staff strongly prefer one or the other.
- Currency (total_amount / monetary metrics): displayed in Toman, formatted with thousands separators appropriate to the active language locale. This is an **internal ops tool**, so unlike customer-facing copy, showing monetary values here is completely fine — the Non-Negotiable Rules (no money words) apply to customer-facing content, not internal dashboards.

### 4.5 Dates

- Store all dates in the warehouse as standard Gregorian/ISO 8601 (as they'll arrive from Navatel).
- **Display** layer: show Jalali (Persian) calendar dates when the UI is in Farsi mode, Gregorian when in English mode — this is a display-only conversion, never a storage format change. A visible small toggle or the language switch itself should control this.

### 4.6 Layout components (dashboard views)

| View | Purpose | Bilingual notes |
|---|---|---|
| **Segment overview** | Bar/donut chart of contact counts per RFM segment | Segment labels shown in Farsi in FA mode ("قهرمانان", "در معرضِ ریزش") with the internal English label as a subtle tooltip for anyone cross-referencing code/docs |
| **Persona distribution** | Counts of نگار / سارا / کیان / امیر / نامشخص guesses | Persona names are already Farsi in both language modes — per `bamipet-personas.md`, persona names are canonical in Farsi, not translated |
| **Customer table** | Filterable/sortable table: contact, segment, persona guess, R/F/M/E, last order, last touch | Column order mirrors per 4.2; filters (segment, persona, journey stage) as dropdowns with Farsi labels in FA mode |
| **Customer drill-down** | Single-contact view: full metric history, segment trend line | Trend line dates in Jalali (FA mode) / Gregorian (EN mode) per 4.5 |
| **Trend over time** | Segment migration — how many contacts moved Champions → At Risk, etc., month over month | Same axis-mirroring exception as 4.2 |

### 4.7 Color & visual tokens

Reuse `bamipet-visual-guidelines.md` tokens directly — this internal tool should still feel like a Bamipet product, not a generic admin panel:

| Token | Hex | Use in this dashboard |
|---|---|---|
| Bamipet Blue `#1C48C1` | Primary | Primary buttons, active nav state, key headings |
| Warm Cream `#FAF9F6` | Base | Dashboard background — **never pure white**, consistent with brand warmth even in an internal tool |
| Calm Green `#2F8F6B` | Affirmative | "Champions" / "Loyal" segment indicators |
| Honey Amber `#B77E33` | Reserved/meaning | Reserve for "needs attention" flags — consistent with its brand role as a trust/attention marker, not decoration |
| Ink `#1A1E2E` | Text | Body text, table content |

A muted red/warning tone (not in the current palette — propose `#C1543A` or similar warm terracotta, staying in the palette's warm register rather than a cold clinical red) should be added for "At Risk / Hibernating" segment indicators, since the existing palette has no designated "danger" color — flag this as a small extension to `bamipet-visual-guidelines.md` if adopted.

### 4.8 Accessibility & practical notes

- Every label, filter, and chart title needs both an English and Farsi string from day one — don't ship English-only and "add Farsi later." Given the team is Farsi-first, treat Farsi as the primary/default language on load, with English as the toggle-to option (opposite of how many products default) — confirm this default with the team, but it matches who will actually use this daily.
- Mixed-content cells (e.g., a customer name in Latin script inside an otherwise-RTL Farsi row) should use `dir="auto"` on that specific cell so script direction resolves correctly without breaking the row's overall RTL flow.

---

## Part 5 — How This Plugs Into the Existing Operating Team

Per `bamipet-operating-team.md`:

- **Marketing & Growth** owns reading this dashboard for ad audience building and funnel reporting — segments feed directly into "which value prop to lead ads with."
- **Strategic Planner** uses persona-distribution views to check pillar weighting is still correct (نگار-weighted pillars ۱/۲ should dominate, per the existing rule).
- **Community & Comms** can use the customer drill-down to prioritize DM/follow-up for high-engagement, low-frequency contacts (nگار-shaped behavior) before they go cold.
- **Brand Strategist** remains the escalation point if any proposed use of a segment (e.g., a win-back campaign) risks brushing against the Non-Negotiable Rules — see the brand-safety note already in the code package's README.

This system does not add a 10th role — it's a shared input, like `bamipet-content-pillars.md`, that multiple existing roles read from.

---

## Part 6 — Open Questions / Dependencies

- [ ] Confirm Navatel's real endpoint paths, base URL, and field names (blocking the sync job — see code package README).
- [ ] Confirm whether in-store sales (currently the majority channel per `bamipet-foundation.md`) flow into Navatel's order/invoice records, or live in a separate POS — if separate, this system only sees the online slice until that's bridged.
- [ ] Confirm whether `species` (cat/dog) exists as a field anywhere in Navatel's schema — needed for the confirmed (not just inferred) کیان mapping.
- [ ] Team decision: default dashboard language on load (Farsi-first proposed in 4.8) — confirm before first build.
- [ ] Team decision: adopt the proposed warning/danger color extension to the visual system (4.7), or pick a different existing token for "At Risk" indicators instead.
- [ ] Hosting decision: where does the small Postgres instance + API layer live — team's existing cloud provider, or a new lightweight setup.

---

*Bamipet RFM+Engagement System — Objective, Architecture & Infrastructure · Level 4 · v1.0 · internal source of truth.*
