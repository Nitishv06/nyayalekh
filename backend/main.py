"""
main.py
NyayaLekh backend. Single FastAPI service that:
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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bns_data import OFFENCES
from llm import extract_facts, match_sections
from pdf_gen import generate_complaint_pdf

app = FastAPI(title="NyayaLekh API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class NarrativeIn(BaseModel):
    narrative: str


class AnalyzeIn(BaseModel):
    facts: dict


class PdfIn(BaseModel):
    facts: dict
    analysis: dict
    language_label: str = "English"


@app.get("/api/health")
def health():
    key_present = bool(os.environ.get("GROQ_API_KEY"))
    return {"status": "ok", "groq_key_configured": key_present}


@app.get("/api/offences")
def offences():
    # Return a UI-safe subset (omit internal ingredient lists if you want a
    # lighter payload; kept here since the frontend shows them for transparency)
    return {"offences": OFFENCES}


@app.post("/api/extract-facts")
def api_extract_facts(body: NarrativeIn):
    if not body.narrative or not body.narrative.strip():
        raise HTTPException(status_code=400, detail="Narrative is empty.")
    try:
        return extract_facts(body.narrative)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fact extraction failed: {e}")


@app.post("/api/analyze")
def api_analyze(body: AnalyzeIn):
    if not body.facts:
        raise HTTPException(status_code=400, detail="Facts are required.")
    try:
        return match_sections(body.facts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Section analysis failed: {e}")


@app.post("/api/generate-pdf")
def api_generate_pdf(body: PdfIn):
    try:
        pdf_bytes = generate_complaint_pdf(body.facts, body.analysis, body.language_label)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=complaint_draft.pdf"},
    )


# --- Static frontend (served last so /api routes above take priority) ---
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
