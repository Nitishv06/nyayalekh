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

## Project structure

```
nyayalekh/
  backend/
    main.py           FastAPI app — API endpoints + serves the frontend
    bns_data.py        Verified BNS/BNSS legal data (the factual backbone)
    llm.py             Claude API calls: fact extraction + section reasoning
    pdf_gen.py          Complaint PDF generation (reportlab)
    requirements.txt
    .env.example
  frontend/
    index.html          4-step single-page app (no build tooling needed)
    style.css
    app.js               API calls + browser speech-to-text (Web Speech API)
  README.md
```

## Run locally (VS Code)

1. Open the `nyayalekh` folder in VS Code.
2. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Get a free API key at https://console.groq.com (no credit card required — sign in with
   Google/GitHub/email, copy the key from API Keys). Copy `.env.example` to `.env` and add
   it, or export it directly:
   ```bash
   export GROQ_API_KEY=gsk_...
   ```
4. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
5. Open **http://localhost:8000** — the backend also serves the frontend, so this is your
   whole app, one URL, no CORS headaches.

## Deploy (for submission)

Any platform that runs a Python web service works. Simplest options:

**Render.com**
- New Web Service → connect your GitHub repo → root directory `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add environment variable `GROQ_API_KEY` in the dashboard

**Railway.app** — same idea, Railway auto-detects the `Procfile`-less Python app; set the
start command as above and add the env var.

**Hugging Face Spaces (Docker)** — if you prefer, wrap this in a simple Dockerfile with the
same start command; Spaces gives you a free public URL quickly.

Whichever you choose: **set `GROQ_API_KEY` as an environment variable on the platform, never
commit it to GitHub.**

## A note on rate limits (since Groq's free tier isn't unlimited)

As of mid-2026, `llama-3.3-70b-versatile` on Groq's free tier allows roughly 30 requests/min
and 1,000 requests/day, with per-minute token caps too. Each complaint you generate uses 2
requests (extract + analyze), so that's ~500 complaints/day of headroom — plenty for building,
testing, and a live demo. If you ever hit a 429 during testing, just wait ~60 seconds; Groq's
limits reset on a rolling window. Exact numbers can change, so check
https://console.groq.com/docs/rate-limits if something feels off.

## Before you submit — checklist

- [ ] Re-verify the 4 BNS sections in `bns_data.py` against a current source (things can be
      amended; I verified as of July 2026).
- [ ] Test all 4 offence scenarios end-to-end (fraud, theft, intimidation, hurt).
- [ ] Confirm the deployed link works from a phone / different device, no login required.
- [ ] `.env` / API key is NOT committed to your public GitHub repo — add `.env` to
      `.gitignore`.
- [ ] Record your 2–3 min demo: messy narrative → extracted facts → section reasoning with
      ingredients shown → generated PDF → the "police must register FIR" payoff line.
- [ ] Write your 1–2 page problem statement (I can draft this next if you want).

## Disclaimer

This tool drafts and structures a complaint based on facts the user provides. It is not
legal advice, and the sections it suggests are not binding on any police officer or court.
The generated PDF states this explicitly — keep that disclaimer in place.
