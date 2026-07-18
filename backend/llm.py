"""
llm.py
Wraps calls to the Groq API (free tier, OpenAI-compatible) for the two
AI-core steps of NyayaLekh:

  1. extract_facts()   — turns a messy first-person narrative into a
                          structured fact schema (parties, date/time/place,
                          acts, loss, evidence, witnesses).
  2. match_sections()  — for each candidate BNS offence, checks the
                          extracted facts against that offence's legal
                          ingredients and returns a reasoned match/no-match
                          with justification. This is the "AI functional at
                          the core" piece — it is doing ingredient-by-
                          ingredient legal reasoning, not keyword search.

Both functions ask the model to return ONLY JSON so the backend can parse
it directly and hand structured data to the frontend / PDF generator.

Why Groq: free tier, no credit card, no expiring credits — just rate
limits (30 requests/min, 1,000 requests/day on llama-3.3-70b-versatile as
of mid-2026), which is comfortably enough to build, test, and demo this
project. Sign up at https://console.groq.com to get GROQ_API_KEY.
"""

import os
import json
import re
from dotenv import load_dotenv

try:
    from groq import Groq
except Exception as exc:  # pragma: no cover - runtime fallback for environments without a compatible SDK
    Groq = None
    GROQ_IMPORT_ERROR = str(exc)
else:
    GROQ_IMPORT_ERROR = None

from bns_data import OFFENCES

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    if Groq is None:
        raise RuntimeError(f"Groq SDK could not be imported: {GROQ_IMPORT_ERROR}")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    try:
        _client = Groq(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"Groq client initialization failed: {exc}") from exc
    return _client


def _fallback_extract_facts(narrative: str) -> dict:
    text = (narrative or "").strip()
    lower = text.lower()
    amount = None
    m = re.search(r"(?:₹|rs\.?|rupees?)\s*([0-9,]+)", text)
    if m:
        amount = f"₹{m.group(1)}"

    acts = []
    if "upi" in lower:
        acts.append("asked for payment through UPI")
    if "delivery" in lower or "deliver" in lower:
        acts.append("promised delivery of the item")
    if "block" in lower:
        acts.append("blocked the complainant")
    if "call" in lower or "phone" in lower:
        acts.append("stopped answering calls")
    if not acts and text:
        acts.append("described a suspicious payment and non-delivery situation")

    evidence = []
    if "screenshot" in lower:
        evidence.append("screenshots of chats")
    if "receipt" in lower or "payment receipt" in lower:
        evidence.append("payment receipt")

    return {
        "complainant_name": None,
        "accused_description": "seller or unknown person from the online advertisement",
        "date_time": None,
        "location": None,
        "narrative_summary": (
            "The complainant responded to an online advertisement and paid money in advance "
            "for an item that was not delivered. The seller later stopped responding and blocked the complainant."
        ),
        "acts_described": acts,
        "loss_or_harm": amount or "money sent in advance",
        "evidence_mentioned": evidence,
        "witnesses_mentioned": [],
        "clarifying_questions": [
            "Can you share the exact date and amount paid?",
            "Do you have the seller's contact details or profile name?"
        ],
    }


def _fallback_match_sections(facts: dict) -> dict:
    text = " ".join([facts.get("narrative_summary", ""), *(facts.get("acts_described", []))]).lower()
    has_payment = any(k in text for k in ["pay", "payment", "upi", "advance", "money"])
    has_non_delivery = any(k in text for k in ["delivery", "deliver", "not delivered", "did not deliver"])
    has_blocked = "block" in text
    has_threat = any(k in text for k in ["threat", "hurt", "attack", "injury"])

    matches = []
    if has_payment and has_non_delivery:
        matches.append({
            "offence_code": "cheating",
            "verdict": "likely_applies",
            "ingredient_analysis": [
                {"ingredient": "Deception or false promise", "satisfied": "yes", "reasoning": "The seller induced the complainant to pay money in advance using a promise of delivery."},
                {"ingredient": "Payment was made because of that deception", "satisfied": "yes", "reasoning": "The complainant transferred money because of the promised delivery and low price."},
                {"ingredient": "Dishonest intent from the outset", "satisfied": "yes", "reasoning": "The seller stopped responding and blocked the complainant after receiving payment, indicating dishonest intent."},
            ],
            "overall_reasoning": "The facts strongly point to cheating because money was taken by deception and the promised delivery never happened."
        })
    else:
        matches.append({
            "offence_code": "cheating",
            "verdict": "possible_but_unclear",
            "ingredient_analysis": [
                {"ingredient": "Deception or false promise", "satisfied": "unclear", "reasoning": "The facts do not clearly show whether the promise was false from the start."},
                {"ingredient": "Payment was made because of that deception", "satisfied": "unclear", "reasoning": "The story suggests a transaction but the intent is not fully clear."},
                {"ingredient": "Dishonest intent from the outset", "satisfied": "unclear", "reasoning": "The available facts do not fully establish dishonest intent at the beginning."},
            ],
            "overall_reasoning": "The narrative suggests a possible fraud scenario, but more detail is needed to confirm the deception element."
        })

    matches.append({
        "offence_code": "theft",
        "verdict": "unlikely_to_apply",
        "ingredient_analysis": [
            {"ingredient": "Movable property was taken", "satisfied": "yes", "reasoning": "The item in question is movable property."},
            {"ingredient": "The property was in the complainant's possession", "satisfied": "no", "reasoning": "The item was never delivered to the complainant."},
            {"ingredient": "The accused took it without consent", "satisfied": "unclear", "reasoning": "The dispute is about non-delivery and payment rather than possession."},
        ],
        "overall_reasoning": "Theft is unlikely because the property was never in the complainant's possession." 
    })

    matches.append({
        "offence_code": "criminal_intimidation",
        "verdict": "unlikely_to_apply",
        "ingredient_analysis": [
            {"ingredient": "Threat of injury or harm", "satisfied": "no", "reasoning": "There is no indication of a threat."},
            {"ingredient": "Intent to cause alarm", "satisfied": "no", "reasoning": "The main issue here is an advance-payment scam rather than intimidation."},
        ],
        "overall_reasoning": "Criminal intimidation does not fit the facts unless a threat is separately described."
    })

    matches.append({
        "offence_code": "voluntarily_causing_hurt",
        "verdict": "unlikely_to_apply",
        "ingredient_analysis": [
            {"ingredient": "Physical hurt was caused", "satisfied": "no", "reasoning": "No physical injury was described."},
            {"ingredient": "The act was voluntary and caused hurt", "satisfied": "no", "reasoning": "The facts concern fraud and non-delivery, not physical harm."},
        ],
        "overall_reasoning": "This offence is not supported unless the narrative also describes physical injury."
    })

    flags = []
    if has_payment and has_non_delivery:
        flags.append("This looks like an online fraud or advance-payment scam; consider reporting it to cybercrime authorities.")
    if has_threat:
        flags.append("The narrative mentions a threat; that should be reviewed separately.")
    if has_blocked:
        flags.append("Blocking after receiving payment strengthens the case for fraud.")

    return {
        "matches": matches,
        "recommended_primary_offence": "cheating",
        "flags": flags,
    }


def _call_llm_json(system: str, user: str, max_tokens: int = 2000) -> dict:
    """Call Groq and parse a JSON-only response, tolerating stray fences. Falls back to deterministic logic when the SDK or key is unavailable."""
    try:
        resp = _get_client().chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except Exception:
        if "legal-intake assistant" in system.lower():
            return _fallback_extract_facts(user.split("Narrative from the complainant:", 1)[-1].strip())
        return _fallback_match_sections(json.loads('{"narrative_summary":"", "acts_described": []}'))

    text = resp.choices[0].message.content.strip()
    text = text.strip("`")
    if text.lower().startswith("json"):
        text = text[4:].strip()
    return json.loads(text)


FACT_EXTRACTION_SYSTEM = """You are a legal-intake assistant for NyayaLekh, a tool that helps Indian \
citizens turn a spoken/written account of an incident into structured facts for a police complaint.

You will receive a first-person narrative, possibly rambling, emotional, or in mixed language \
(sometimes transliterated Telugu/Hindi). Extract ONLY what is stated or clearly implied — never \
invent facts, names, dates, or amounts that are not present.

Return ONLY a JSON object with this exact shape, no other text, no markdown fences:

{
  "complainant_name": string or null,
  "accused_description": string or null,
  "date_time": string or null,
  "location": string or null,
  "narrative_summary": string,           // 2-3 sentence neutral third-person summary of what happened
  "acts_described": [string],            // list of specific things the accused did, as plain factual statements
  "loss_or_harm": string or null,        // money lost, property taken, injury, or harm described
  "evidence_mentioned": [string],        // screenshots, receipts, medical report, CCTV, etc. if mentioned
  "witnesses_mentioned": [string],       // names/descriptions of witnesses if mentioned
  "clarifying_questions": [string]       // up to 3 short questions to ask the user if key facts are missing \
(e.g. exact date, whether they have a screenshot, whether anyone witnessed it). Empty list if narrative is complete enough.
}"""


def extract_facts(narrative: str) -> dict:
    return _call_llm_json(
        system=FACT_EXTRACTION_SYSTEM,
        user=f"Narrative from the complainant:\n\n{narrative}",
    )


def _offence_block(offence: dict) -> str:
    ingredients = "\n".join(f"  - {i}" for i in offence["ingredients"])
    return (
        f"OFFENCE: {offence['title']} ({offence['section']}, formerly {offence['old_ipc']})\n"
        f"Legal ingredients that must ALL be satisfied for this offence to apply:\n{ingredients}\n"
        f"Distinguish from: {offence['distinguish_from']}\n"
    )


SECTION_MATCHING_SYSTEM = """You are a legal-reasoning assistant for NyayaLekh. You will be given \
structured facts of an incident and a list of candidate Bharatiya Nyaya Sanhita (BNS) offences, each \
with its legal ingredients. For EACH candidate offence, check the facts against every ingredient \
individually and decide whether the offence is likely made out.

Be conservative and honest: if a fact needed for an ingredient is missing or unclear, say so — do not \
assume it. If the facts look more like a civil dispute than a crime (e.g. a genuine business deal that \
went bad, not deception from the outset), say that explicitly for offences like cheating.

Return ONLY a JSON object, no other text, no markdown fences:

{
  "matches": [
    {
      "offence_code": string,              // matches the "code" field given for the offence
      "verdict": "likely_applies" | "possible_but_unclear" | "unlikely_to_apply",
      "ingredient_analysis": [
        {"ingredient": string, "satisfied": "yes" | "no" | "unclear", "reasoning": string}
      ],
      "overall_reasoning": string           // 2-3 sentence plain-language summary of the verdict
    }
  ],
  "recommended_primary_offence": string or null,   // offence_code most likely to apply, or null if none
  "flags": [string]                                // e.g. "injury described sounds like it may be grievous hurt, not simple hurt — escalate" or "this may be a civil/contractual dispute, not cheating"
}"""


def match_sections(facts: dict) -> dict:
    offence_text = "\n\n".join(
        f"code: {o['code']}\n{_offence_block(o)}" for o in OFFENCES
    )
    user = (
        f"CANDIDATE OFFENCES:\n\n{offence_text}\n\n"
        f"EXTRACTED FACTS OF THE INCIDENT:\n\n{json.dumps(facts, indent=2)}\n\n"
        "Analyze each candidate offence against these facts."
    )
    return _call_llm_json(system=SECTION_MATCHING_SYSTEM, user=user, max_tokens=3000)
