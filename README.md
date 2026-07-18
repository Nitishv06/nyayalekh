# NyayaLekh — AI Complaint Drafter for India's New Criminal Law Era

An AI tool that turns a citizen's messy, spoken account of an incident into a structured,
section-mapped, station-ready police complaint under the Bharatiya Nyaya Sanhita (BNS), 2023.

Built for Idea2Impact 2026 · Theme 1 (Sustainability & Social Impact — Financial/Legal Inclusion)

---

## How it works (the AI pipeline)

1. **Narrative intake** — user speaks or types what happened, in plain language.
2. **Fact extraction** (`POST /api/extract-facts`) — Claude extracts structured facts
   (parties, date/time/place, acts, loss, evidence, witnesses) from the raw narrative.
3. **Section-matching reasoning** (`POST /api/analyze`) — Claude checks the extracted facts
   against the actual legal *ingredients* of 4 BNS offences (cheating, theft, criminal
   intimidation, voluntarily causing hurt) and returns a reasoned verdict per offence,
   with ingredient-by-ingredient justification — not keyword matching.
4. **Complaint generation** (`POST /api/generate-pdf`) — a formal, station-ready PDF is
   generated with the facts in chronological order, applicable sections with reasoning,
   BNSS procedural rights (Zero FIR / e-FIR / cognizable vs non-cognizable routing), an
   evidence checklist, and a disclaimer.

The legal data in `backend/bns_data.py` was manually verified against multiple independent
legal sources (July 2026) — the LLM never invents section numbers; it only reasons over the
verified ingredients you give it. **Re-verify before your demo** if you add more offences.


## A note on rate limits (since Groq's free tier isn't unlimited)

As of mid-2026, `llama-3.3-70b-versatile` on Groq's free tier allows roughly 30 requests/min
and 1,000 requests/day, with per-minute token caps too. Each complaint you generate uses 2
requests (extract + analyze), so that's ~500 complaints/day of headroom — plenty for building,
testing, and a live demo. If you ever hit a 429 during testing, just wait ~60 seconds; Groq's
limits reset on a rolling window. Exact numbers can change, so check
https://console.groq.com/docs/rate-limits if something feels off.

## Disclaimer

This tool drafts and structures a complaint based on facts the user provides. It is not
legal advice, and the sections it suggests are not binding on any police officer or court.
The generated PDF states this explicitly — keep that disclaimer in place.
