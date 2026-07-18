"""
main.py
NyayaLekh backend. Single ASGI service that:
  1. Serves the static frontend (so you deploy ONE service, not two).
  2. Exposes the AI pipeline as three endpoints:
       POST /api/extract-facts   -> structured facts from narrative
       POST /api/analyze         -> BNS section matching + reasoning
       POST /api/generate-pdf    -> final complaint PDF
  3. /api/offences               -> the 4 supported offences (for UI display)
  4. /api/health                 -> quick check for deploy debugging
"""

import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from bns_data import OFFENCES
from llm import extract_facts, match_sections
from pdf_gen import generate_complaint_pdf

app = Starlette()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


async def health(request: Request):
    key_present = bool(os.environ.get("GROQ_API_KEY"))
    return JSONResponse({"status": "ok", "groq_key_configured": key_present})


async def offences(request: Request):
    return JSONResponse({"offences": OFFENCES})


async def api_extract_facts(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body."}, status_code=400)

    narrative = payload.get("narrative") if isinstance(payload, dict) else None
    if not isinstance(narrative, str) or not narrative.strip():
        return JSONResponse({"detail": "Narrative is empty."}, status_code=400)

    try:
        return JSONResponse(extract_facts(narrative))
    except Exception as e:
        return JSONResponse({"detail": f"Fact extraction failed: {e}"}, status_code=500)


async def api_analyze(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body."}, status_code=400)

    facts = payload.get("facts") if isinstance(payload, dict) else None
    if not isinstance(facts, dict) or not facts:
        return JSONResponse({"detail": "Facts are required."}, status_code=400)

    try:
        return JSONResponse(match_sections(facts))
    except Exception as e:
        return JSONResponse({"detail": f"Section analysis failed: {e}"}, status_code=500)


async def api_generate_pdf(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body."}, status_code=400)

    if not isinstance(payload, dict):
        return JSONResponse({"detail": "Invalid request body."}, status_code=400)

    facts = payload.get("facts")
    analysis = payload.get("analysis")
    language_label = payload.get("language_label", "English")

    if not isinstance(facts, dict) or not isinstance(analysis, dict):
        return JSONResponse({"detail": "Facts and analysis are required."}, status_code=400)

    try:
        pdf_bytes = generate_complaint_pdf(facts, analysis, language_label)
    except Exception as e:
        return JSONResponse({"detail": f"PDF generation failed: {e}"}, status_code=500)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=complaint_draft.pdf"},
    )


routes = [
    Route("/api/health", health, methods=["GET"]),
    Route("/api/offences", offences, methods=["GET"]),
    Route("/api/extract-facts", api_extract_facts, methods=["POST"]),
    Route("/api/analyze", api_analyze, methods=["POST"]),
    Route("/api/generate-pdf", api_generate_pdf, methods=["POST"]),
]

app.router.routes.extend(routes)

# --- Static frontend (served last so /api routes above take priority) ---
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
