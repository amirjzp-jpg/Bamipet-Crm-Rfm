# Bamipet × Navatel — RFM+Engagement Engine

Segments Bamipet's customers using Recency, Frequency, Monetary (standard RFM)
**plus Engagement** (call + SMS volume/recency) — since Navatel is a unified
CRM/telephony/SMS platform, not just an order database. Also produces a
best-guess mapping from each segment to a Bamipet persona (نگار/سارا/کیان/امیر)
and the messaging pillar to lead with, per `bamipet-messaging-architecture.md`.

> **Building this into a full product?** Start with
> [`bamipet-rfm-build-plan.md`](./bamipet-rfm-build-plan.md) — the concrete,
> execution-ready engineering plan (tech stack, data model, API contract,
> page-by-page UI spec, phased build order, and the current gap list against
> this repo). `bamipet-rfm-system-spec.md` remains the architecture/UX
> source of truth; the build plan operationalizes it.

## What's here

| File | Purpose |
|---|---|
| `config.py` | Base URL, token, endpoint paths, RFM window — **3 things to confirm** |
| `navatel_client.py` | REST adapter (contacts, orders, calls, SMS, write-back) |
| `rfm_engine.py` | Builds the customer table and computes R/F/M/E scores + segment label |
| `persona_mapper.py` | Segment → Bamipet persona guess → lead pillar → journey stage |
| `main.py` | Runs the full pipeline end to end |

## Before running: 3 things to confirm from Navatel's Swagger docs

Navatel's own architecture writeup confirms API-First + OpenAPI/Swagger docs
exist, just not publicly indexed — they're in the panel at `cp.navatel.ir`,
under the API/webservice section. Once you're logged in there:

1. **Base URL** — the `servers` block at the top of the Swagger doc. Set as env var `NAVATEL_BASE_URL`.
2. **The 4 endpoint paths** in `config.py` → `ENDPOINTS` — contacts, orders/invoices, call logs, SMS logs. Given the microservice split they describe (Call Service / Messaging Service / CRM Service), expect these on genuinely different paths.
3. **Field names** — `rfm_engine.py` assumes fields like `id`, `contact_id`, `amount`, `created_at`. Rename in `build_customer_table` to match whatever the real schema calls them (visible in each endpoint's Swagger response schema).

Everything else (scoring math, segment logic, persona mapping) works as-is
once those three are correct.

## Setup

```bash
pip install -r requirements.txt
export NAVATEL_BASE_URL="https://<real-gateway-host>"
export NAVATEL_API_TOKEN="<token from panel>"
python main.py
```

Write-back to Navatel (`client.update_contact_field(...)`) is commented out
in `main.py` by default — uncomment only after confirming `bamipet_rfm_segment`
and `bamipet_persona_guess` exist as real custom fields on a contact (or
create them in the panel first).

## Segment → Persona → Messaging map

| RFM+E Segment | Likely persona | Journey stage | Lead pillar |
|---|---|---|---|
| Champions | سارا (if high $, low support contact) | وفاداری | ۴ · در تمامِ مسیر کنارتیم |
| Loyal Customers | سارا / نگار (graduated) | وفاداری | ۴ |
| New Customers, high call/SMS volume | **نگار** | سنجش | ۱ + ۳ |
| Promising | امیر (if decisive, low engagement) | سنجش | ۲ |
| Needs Attention | mixed | تصمیم | ۲ + ۳ |
| At Risk / Can't Lose Them | mixed | تصمیم | ۴ (reconnection, **not discount**) |
| Hibernating / Lost | مبهم | آگاهی | ۳ (soft re-intro) |
| species = dog (if field exists) | **کیان** | — | ۴ + ۲ (overrides default) |

Full reasoning for each rule is in the docstrings inside `persona_mapper.py`.

## ⚠️ Brand-safety note — read before this touches any campaign

This segmentation is analytics, not copy. Whatever channel it feeds — an
SMS blast through Navatel's own messaging panel, an ad audience, a DM script
— **the actual words still have to pass `bamipet-voice-message-copy.md`'s
Pre-Publish Checklist.** The one segment most likely to get misused is
**At Risk / Hibernating**: the standard e-commerce move is a discount SMS
("بازگرد و ۱۵٪ تخفیف بگیر"), and that directly breaks Bamipet's Non-Negotiable
Rules (no money words, ever). A win-back message to this segment should be
pillar ۴ reassurance/reconnection — "دلمون برای همراهت تنگ شده، حالش چطوره؟" —
never a coupon code.

## Known gaps / assumptions to validate with real data

- Assumes `species` (cat/dog) isn't reliably in the schema yet — the کیان
  mapping is a bonus rule that activates *if* that field exists, and falls
  back to behavior-only inference otherwise.
- Assumes in-store purchases (currently the majority of Bamipet's volume per
  the Foundation doc) also flow into Navatel's order/invoice records. If
  in-store sales live in a separate POS system, this pipeline will only see
  the online slice and segments will skew — worth confirming early.
- Quintile scoring (`pd.qcut`) needs a reasonably-sized customer base to
  produce 5 clean bins; `rfm_engine.py` degrades gracefully to fewer bins on
  small/sparse data, but interpret early runs with that in mind.
