"""Single registry for the nine RFM segments and four personas — internal
code label, Farsi/English display labels, and dashboard color token (build
plan Part 4). The frontend never hardcodes these: it fetches them from
GET /api/v1/segments/meta so Python stays the one source of truth.

Colors come from bamipet-visual-guidelines.md. Terracotta #C1543A is the
proposed "at risk" extension from the spec (§4.7) — pending team sign-off,
swap here if a different token is chosen.
"""
from __future__ import annotations

# Ordered from best to worst — the dashboard preserves this ordering in
# legends and tables so the team reads the list as a health gradient.
SEGMENTS: list[dict] = [
    {"code": "Champions", "fa": "قهرمانان", "en": "Champions", "color": "#2F8F6B", "tone": "positive"},
    {"code": "Loyal Customers", "fa": "مشتریانِ وفادار", "en": "Loyal Customers", "color": "#2F8F6B", "tone": "positive"},
    {"code": "New Customers", "fa": "مشتریانِ جدید", "en": "New Customers", "color": "#1C48C1", "tone": "primary"},
    {"code": "Promising", "fa": "امیدبخش", "en": "Promising", "color": "#2E5BE0", "tone": "primary"},
    {"code": "Needs Attention", "fa": "نیازمندِ توجه", "en": "Needs Attention", "color": "#B77E33", "tone": "attention"},
    {"code": "About To Sleep", "fa": "در آستانهٔ رکود", "en": "About To Sleep", "color": "#B77E33", "tone": "attention"},
    {"code": "At Risk", "fa": "در معرضِ ریزش", "en": "At Risk", "color": "#C1543A", "tone": "danger"},
    {"code": "Can't Lose Them", "fa": "نبایدشان را از دست داد", "en": "Can't Lose Them", "color": "#C1543A", "tone": "danger"},
    {"code": "Hibernating / Lost", "fa": "به‌خواب‌رفته", "en": "Hibernating / Lost", "color": "#8B93A5", "tone": "muted"},
]

# Persona names are canonical in Farsi in BOTH language modes
# (bamipet-personas.md: persona names are never translated).
PERSONAS: list[dict] = [
    {"code": "نگار", "fa": "نگار", "en": "نگار", "color": "#1C48C1", "description_en": "Anxious first-timer", "description_fa": "سرپرستِ نگرانِ تازه‌کار"},
    {"code": "سارا", "fa": "سارا", "en": "سارا", "color": "#2F8F6B", "description_en": "Seasoned guardian", "description_fa": "سرپرستِ باتجربه"},
    {"code": "کیان", "fa": "کیان", "en": "کیان", "color": "#B77E33", "description_en": "Devoted dog parent", "description_fa": "سرپرستِ فداکارِ سگ"},
    {"code": "امیر", "fa": "امیر", "en": "امیر", "color": "#123086", "description_en": "Pragmatic buyer", "description_fa": "خریدارِ عمل‌گرا"},
    {"code": "نامشخص", "fa": "نامشخص", "en": "نامشخص", "color": "#8B93A5", "description_en": "Unclear — treat as نگار-safe", "description_fa": "سیگنالِ رفتاری نامشخص"},
]

JOURNEY_STAGES: list[dict] = [
    {"code": "آگاهی", "fa": "آگاهی", "en": "Awareness"},
    {"code": "سنجش", "fa": "سنجش", "en": "Consideration"},
    {"code": "تصمیم", "fa": "تصمیم", "en": "Decision"},
    {"code": "وفاداری", "fa": "وفاداری", "en": "Loyalty"},
]

SEGMENT_CODES = [s["code"] for s in SEGMENTS]
PERSONA_CODES = [p["code"] for p in PERSONAS]
SEGMENT_BY_CODE = {s["code"]: s for s in SEGMENTS}
