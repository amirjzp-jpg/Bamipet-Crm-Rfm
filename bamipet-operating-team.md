# Bamipet — Operating Team & Workflow · تیمِ عملیاتی و گردشِ کار (Level 4 · Operations)

> **How to use this file.** This defines the full operational function needed to run Bamipet's brand, content, and marketing engine — whether staffed by people, by Claude acting in different roles, or a mix of both. For any task:
> 1. Identify **which role** the task belongs to (see *The Nine Roles*).
> 2. Pull the **exact project files** that role depends on — listed under each role.
> 3. Follow the **pipeline stage** the task sits in (idea → strategy gate → creation → production → brand QA → publish → measure).
> 4. Every role, without exception, obeys the **Cross-Functional Constitution** below — this is the one section no role may skip.
> 5. If asked to "act as" a specific role, adopt that role's mandate and inputs fully for the task, then hand off cleanly per the pipeline.
>
> This file sits **above** all other Bamipet documents — it's the operating system that tells the team (human or AI) *how* to use everything else. Full document map at the end.

---

## Why This Exists

Eight documents of strategy, voice, and execution guidance are only as good as the workflow that uses them. This file closes that gap: it defines **who does what, with which inputs, checked by whom, before anything reaches a customer.** The recurring audit problems earlier in this project (bazaar language, money words, self-praise) happened because content was created without a clear pipeline or a final brand-check gate. This file is that gate.

---

# The Nine Roles

Each role has a mandate, the exact files it draws from, its output, and its non-negotiables.

## 1 · راهبردِ برند — Brand Strategist
**Mandate:** Owns brand coherence across everything. Approves new campaigns, resolves conflicts between commercial pressure and brand rules, decides when strategy itself needs revisiting (not just execution).
**Inputs:** `bamipet-foundation.md`, `bamipet-personas.md`, `bamipet-value-proposition.md` (within voice-message-copy), Onliness Statement.
**Output:** Go/no-go on strategic direction; resolves "is this still on-brand" escalations.
**Rule:** Has final say on anything that touches the Non-Negotiable Rules or North Star — no other role overrides this one.

## 2 · ایده‌پرداز — Ideation Lead
**Mandate:** Generates the raw pool of content ideas across all five pillars, spots trends worth adapting (never copying), keeps the idea pipeline full so creation never stalls.
**Inputs:** `bamipet-content-pillars.md` (pillars + formats + weighting), `bamipet-personas.md` (persona needs), `bamipet-instagram-playbook.md` Part Three (reference accounts for pattern-matching, never copying).
**Output:** A running backlog of ideas tagged by pillar, format, and target persona.
**Rule:** Every idea must trace to a real persona need or value prop — no idea "because it's trendy" alone.

## 3 · برنامه‌ریزِ راهبردی — Strategic Planner
**Mandate:** Turns the idea backlog into an actual calendar — sequencing, weighting pillars correctly, aligning with journey stages and seasonal/business moments.
**Inputs:** `bamipet-content-pillars.md` (weighting, governance cadence), `bamipet-messaging-architecture.md` (journey-stage messaging), `bamipet-instagram-playbook.md` Part Four (calendar template).
**Output:** The scheduled content calendar (weekly/monthly).
**Rule:** نگار-weighted pillars (۱ and ۲) always dominate the schedule; پیلار ۵ (dogs) stays present but never crowds the cat-first feed.

## 4 · کپی‌رایتر — Copywriter
**Mandate:** Writes every word a customer reads — captions, scripts, product copy, replies, ads.
**Inputs:** `bamipet-voice-message-copy.md` (voice, phrase bank, templates, rewrite recipe), `bamipet-messaging-architecture.md` (which value prop/angle to lead with).
**Output:** Finished, on-voice copy for any format.
**Rule:** Must run every piece through the Pre-Publish Checklist in `bamipet-voice-message-copy.md` before handing off — this is not optional and not the QA role's job to catch first.

## 5 · مهندسِ پرامپت — AI Prompt Engineer
**Mandate:** Produces AI-generated visual/video assets (backgrounds, illustrations, concept art, product mockups) using the correct tool for the job.
**Inputs:** `bamipet-visual-guidelines.md` (palette, mood, logo rules), `bamipet-instagram-playbook.md` Part Five (tool map, prompt templates, guardrails).
**Output:** AI-generated visual assets, ready for the Visual Designer to finish (Farsi text, brand framing).
**Rule:** Never generates Farsi text via AI model (unreliable rendering) — always generates the visual clean, hands off for text to be added separately. Never produces an asset that could be mistaken for real customer/product photography without disclosure internally.

## 6 · تیمِ ویدئو — Video Team
**Mandate:** Produces and edits Reels and any video content — filming real footage, editing AI-generated video elements together, ensuring hook/pacing/caption standards are met.
**Inputs:** `bamipet-instagram-playbook.md` Part Two (Reels specs: hook window, length-by-goal, safe zones, hook formula), `bamipet-voice-message-copy.md` (tone in scripts).
**Output:** Finished, published-ready Reels.
**Rule:** Real footage of real guardians/companions is the default; AI-generated video is a supporting element only (intros, transitions, backgrounds), consistent with the "raw human content" algorithm preference.

## 7 · طراحِ بصری — Visual Designer
**Mandate:** Builds every static visual asset — carousels, product tags, story templates, feed graphics — ensuring the visual system from `bamipet-visual-guidelines.md` is applied correctly and consistently.
**Inputs:** `bamipet-visual-guidelines.md` (full system: logo, palette, type, tokens), AI Prompt Engineer's raw outputs (to finish/adapt).
**Output:** Publish-ready visual assets in final brand form.
**Rule:** Owns the "does this look like Bamipet" check — logo misuse, off-palette colors, and cramped/cluttered layouts get caught here before anything moves downstream.

## 8 · تیمِ ارتباطات — Community & Comms
**Mandate:** Handles every direct interaction — DMs, comments, Story replies — and owns response speed (a direct 2026 ranking factor).
**Inputs:** `bamipet-voice-message-copy.md` (support-reply templates, phrase bank), `bamipet-instagram-playbook.md` Part One (relationship-score/response-speed rule).
**Output:** Timely, on-voice responses to every interaction.
**Rule:** Fast response is not just service quality — it's an algorithmic lever (response speed strengthens the relationship score that boosts future content visibility for that follower). Never leave a DM or comment unanswered past a same-day window if avoidable.

## 9 · بازاریابی و رشد — Marketing & Growth
**Mandate:** Owns paid acquisition, website/SEO health, and performance measurement across the whole funnel — the layer connecting content to actual business outcomes.
**Inputs:** `bamipet-seo-crawl-setup.md` (technical SEO/AEO), `bamipet-messaging-architecture.md` (journey-stage and surface-lead mapping), `bamipet-value-proposition.md` (which prop to lead ads with — always #3, the wedge).
**Output:** Website health, ad campaigns, funnel performance reporting.
**Rule:** Ad copy obeys the same Non-Negotiable Rules as organic content — performance pressure never overrides the no-money/no-self-praise rules.

---

# The Pipeline — How Work Actually Flows

```
IDEA  →  STRATEGY GATE  →  CREATION  →  PRODUCTION  →  BRAND QA  →  PUBLISH  →  MEASURE
 (2)        (1 / 3)           (4)         (5/6/7)         (—)         (8/9)      (3/9)
```

1. **Idea** — Ideation Lead generates a backlog item, tagged to pillar + persona + format.
2. **Strategy Gate** — Strategic Planner slots it into the calendar; Brand Strategist flags anything that needs a strategic call (new territory, sensitive topic, competitive claim).
3. **Creation** — Copywriter drafts the words; runs the Pre-Publish Checklist.
4. **Production** — AI Prompt Engineer and/or Video Team and Visual Designer build the actual asset, matching Visual Guidelines.
5. **Brand QA** — A final check against the *full* Cross-Functional Constitution below (not just voice — visual, dignity, money-language, everything). **No single creator approves their own final output** — a second set of eyes (any other role, or the Brand Strategist for anything sensitive) does this pass.
6. **Publish** — Comms team owns the post going live and the interactions that follow.
7. **Measure** — Marketing & Growth and Strategic Planner review performance (Sends, Saves, Watch Time — not vanity likes) and feed learnings back into Ideation.

**This loop is continuous.** Step 7 always feeds back into Step 1.

---

# Cross-Functional Constitution

**Every role, every piece of output, no exceptions.** This consolidates the hardest-won rules from across the whole project — the ones that broke most often before this operational layer existed.

1. **Never name money, price, budget, discount, or "the sale"** in customer-facing content. Affordability is conveyed only as reassurance (see Value Prop ۳).
2. **Never self-praise or announce your own honesty.** Show it through behavior and proof, not claims.
3. **Every sentence is about the سرپرست and همراه — never about Bamipet's own greatness.**
4. **Use سرپرست, never صاحب/خریدار. Use همراه, never a dehumanizing term. Never توله — use بچه‌گربه/بچه‌سگ or the age.**
5. **Warm but composed — never bazaar-casual** (no الکی, بندازم, or similar). A caring expert, not a shopkeeper.
6. **Cat-first, dog-inclusive.** نگار and cat content lead; dog content (پیلار ۵) has a real, respected space but never dominates.
7. **Never expose internal strategy language** (دشمنِ برند, ستارهٔ راهنود, "تأییدِ بامی" as jargon, persona names) in anything customer-facing.
8. **Never fabricate authenticity.** AI-generated content is never presented as real photography; UGC is only ever real.
9. **Every claim about the brand's differentiation resolves to:** *does this turn an anxious guardian into a confident one?* (the North Star). If a piece of content doesn't serve that, it doesn't ship.

---

# Cadence

| Frequency | What happens | Who |
|---|---|---|
| **Daily** | Stories (3–7), DM/comment response | Comms |
| **Weekly** | Content calendar execution (~3 Reels, 1 Carousel, 1 Post) | Planner, Copywriter, Video, Design |
| **Monthly** | Performance pulse — what worked, double down | Planner, Marketing |
| **Quarterly** | Deep review against goals; retire or rebuild weak pillars; revisit weighting | Strategist, Planner |
| **Event-driven** | New product launch, platform algorithm shift, brand-sensitive moment | Strategist (escalation point) |

---

# Activating a Role in This Project

When working within the Bamipet Claude Project, a task can explicitly invoke a role to load the right context automatically. Examples:

- *"As Ideation Lead, give me 10 Reel ideas for پیلار ۱ targeting نگار."* → pulls content-pillars + personas.
- *"As Copywriter, write an Instagram caption for [product] using the safe product-intro template."* → pulls voice-message-copy + content-pillars template.
- *"As AI Prompt Engineer, build a prompt for a carousel background about choosing cat litter."* → pulls visual-guidelines + Instagram playbook Part Five.
- *"As Brand QA, review this draft against the full Constitution before it ships."* → runs the Pre-Publish Checklist + Constitution above, flags anything.
- *"As Marketing & Growth, what should this month's ad lead with?"* → pulls value-proposition + messaging-architecture journey stages.

This lets one person (or one model) reliably produce specialist-quality output across every function, because the *inputs* are already mapped — no guessing which document applies.

---

# Full Document Map

| File | Primary owner(s) | Used by |
|---|---|---|
| `bamipet-foundation.md` | Brand Strategist | All roles (root strategy) |
| `bamipet-personas.md` | Ideation, Strategist | Ideation, Planner, Copywriter |
| `bamipet-voice-message-copy.md` | Copywriter | Copywriter, Comms, Video (scripts) |
| `bamipet-messaging-architecture.md` | Planner, Marketing | Planner, Marketing, Copywriter |
| `bamipet-content-pillars.md` | Ideation, Planner | Ideation, Planner, Video, Design |
| `bamipet-visual-guidelines.md` | Visual Designer | Designer, AI Prompt Engineer |
| `bamipet-instagram-playbook.md` | Planner, Video, AI Prompt Engineer | Planner, Video, Designer, Prompt Engineer |
| `bamipet-seo-crawl-setup.md` | Marketing & Growth | Marketing, Strategist |
| *(this file)* | All | The operating layer connecting all of the above |

---

## Notes

- This structure works whether Bamipet staffs these as **distinct people**, **combined roles** (e.g., one person covering Copywriter + Comms), or **AI-assisted** via this Claude Project acting in different roles per task.
- The **Brand QA step is the single most important addition** this file makes — every prior audit issue in this project happened because content skipped a genuine second-look before publishing. No role should self-approve final output.
- As the team scales or roles consolidate, update the *role → file* mapping above rather than letting any role operate without a defined input set.

---

*Bamipet Operating Team & Workflow · Level 4 · v1.0 · internal source of truth.*
