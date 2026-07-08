"""
Maps each RFM+E segment onto a Bamipet persona, lead messaging pillar, and
journey stage -- so Marketing & Growth / Copywriter roles know which angle
to write in, per bamipet-personas.md and bamipet-messaging-architecture.md.

This is a heuristic, not a certainty -- Navatel's contact/order schema may
or may not carry species (cat/dog) or channel (online/in-store) fields. Two
confidence tiers are returned:
  - "confirmed" persona hints (species-based, when that field exists)
  - "inferred" persona hints (behavior-based, from RFM+E shape alone)

IMPORTANT (Non-Negotiable Rules still apply downstream): whatever this
mapping is used for -- SMS via Navatel's messaging panel, ads, DMs -- the
actual copy must still pass bamipet-voice-message-copy.md's Pre-Publish
Checklist. In particular: "At Risk" / "Hibernating" segments are a natural
target for win-back SMS, but a win-back message must NEVER be a discount
code. Frame it as pillar 4 (در تمامِ مسیر کنارتیم) reassurance/reconnection,
never as "بازگرد و تخفیف بگیر."
"""
from dataclasses import dataclass


@dataclass
class PersonaGuess:
    segment: str
    likely_persona: str          # نگار / سارا / کیان / امیر / "نامشخص"
    confidence: str              # "confirmed" | "inferred"
    lead_pillar: str             # from bamipet-messaging-architecture.md
    journey_stage: str           # آگاهی / سنجش / تصمیم / وفاداری
    note: str


# RFM segment -> default journey stage + pillar, before persona refinement
_SEGMENT_DEFAULTS = {
    "Champions":          ("وفاداری", "۴ · در تمامِ مسیر کنارتیم"),
    "Loyal Customers":     ("وفاداری", "۴ · در تمامِ مسیر کنارتیم"),
    "New Customers":       ("سنجش", "۱ + ۳ · راهنمایی صادقانه + خیالِ راحت از انتخاب"),
    "Promising":           ("سنجش", "۲ · بررسی‌شده و اصل"),
    "Needs Attention":     ("تصمیم", "۲ + ۳ · اصالت + خیالِ راحت از انتخاب"),
    "At Risk":             ("تصمیم", "۴ · در تمامِ مسیر کنارتیم (بدونِ تخفیف)"),
    "Can't Lose Them":     ("تصمیم", "۴ · در تمامِ مسیر کنارتیم (بدونِ تخفیف)"),
    "Hibernating / Lost":  ("آگاهی", "۳ · خیالِ راحت از انتخاب (بازآشناییِ نرم)"),
    "About To Sleep":      ("تصمیم", "۱ · راهنماییِ صادقانه و دلسوز"),
}


def guess_persona(row, species: str = None) -> PersonaGuess:
    """`row` is one row from the scored RFM+E table (rfm_engine.score_rfm).
    `species` is optional -- pass it in if/when Navatel's contact or order
    schema exposes a cat/dog field; leave None to fall back to behavior-only
    inference."""
    segment = row["rfm_segment"]
    stage, pillar = _SEGMENT_DEFAULTS.get(segment, ("سنجش", "۳ · خیالِ راحت از انتخاب"))

    # Confirmed: species field exists and says dog -> کیان, regardless of RFM shape
    if species == "dog":
        return PersonaGuess(segment, "کیان", "confirmed", "۴ + ۲ · اطمینانِ تأمین + اصالت", stage,
                             "Species field confirms dog -- کیان's lead pillars override the default RFM pillar.")

    # Inferred, from behavior shape only:
    high_engagement = row["E"] >= 4        # lots of calls/SMS relative to peers
    low_frequency = row["F"] <= 2
    high_frequency = row["F"] >= 4
    high_monetary = row["M"] >= 4

    if segment == "New Customers" and high_engagement:
        return PersonaGuess(segment, "نگار", "inferred", pillar, stage,
                             "New + high call/SMS volume before/around first purchase matches نگار's two-layer worry pattern -- lots of questions, still deciding.")

    if high_frequency and high_monetary and not high_engagement:
        return PersonaGuess(segment, "سارا", "inferred", pillar, stage,
                             "Frequent, high-spend, but low support-contact volume matches سارا -- she already knows what she wants and rarely needs hand-holding.")

    if low_frequency and high_monetary and not high_engagement:
        return PersonaGuess(segment, "امیر", "inferred", pillar, stage,
                             "Infrequent but decisive high-value orders with minimal engagement matches امیر -- efficient, doesn't linger on the decision.")

    return PersonaGuess(segment, "نامشخص", "inferred", pillar, stage,
                         "No strong behavioral signal either way -- default to نگار-safe tone (the base-rate persona) until more data accumulates.")
