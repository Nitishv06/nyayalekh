"""
pdf_gen.py
Generates the final downloadable complaint PDF: a formal, station-ready
letter with facts in chronological order, applicable BNS sections with
brief reasoning, an evidence checklist, and a disclaimer.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib import colors

from bns_data import OFFENCES, BNSS_PROCEDURE

OFFENCE_BY_CODE = {o["code"]: o for o in OFFENCES}

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ComplaintTitle", fontSize=15, leading=19,
                           spaceAfter=10, alignment=TA_JUSTIFY, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="SectionHeading", fontSize=12, leading=15,
                           spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#1B2A41")))
styles.add(ParagraphStyle(name="Body", fontSize=10.5, leading=15,
                           alignment=TA_JUSTIFY, fontName="Helvetica"))
styles.add(ParagraphStyle(name="Small", fontSize=8.5, leading=12,
                           textColor=colors.HexColor("#555555")))


def generate_complaint_pdf(facts: dict, analysis: dict, language_label: str = "English") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    story = []

    story.append(Paragraph("To,", styles["Body"]))
    story.append(Paragraph("The Station House Officer,", styles["Body"]))
    story.append(Paragraph("[Police Station Name — fill in / any station under Zero FIR], Telangana", styles["Body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}", styles["Body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Subject: Complaint regarding a criminal offence — request for registration of FIR",
                            styles["ComplaintTitle"]))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#C08A28"), thickness=1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Respected Sir/Madam,", styles["Body"]))
    story.append(Spacer(1, 6))

    intro = (
        f"I, {facts.get('complainant_name') or '[Complainant Name]'}, wish to lodge a complaint "
        f"regarding an incident that occurred on {facts.get('date_time') or '[date/time to be confirmed]'} "
        f"at {facts.get('location') or '[location to be confirmed]'}. The facts of the matter are as follows:"
    )
    story.append(Paragraph(intro, styles["Body"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(facts.get("narrative_summary", ""), styles["Body"]))

    if facts.get("acts_described"):
        story.append(Paragraph("Sequence of events:", styles["SectionHeading"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(a, styles["Body"])) for a in facts["acts_described"]],
            bulletType="1",
        ))

    if facts.get("loss_or_harm"):
        story.append(Paragraph("Loss / harm suffered:", styles["SectionHeading"]))
        story.append(Paragraph(facts["loss_or_harm"], styles["Body"]))

    accused_desc = facts.get("accused_description")
    if accused_desc:
        story.append(Paragraph("Details of the accused (to the extent known):", styles["SectionHeading"]))
        story.append(Paragraph(accused_desc, styles["Body"]))

    story.append(Paragraph("Applicable provisions of law", styles["SectionHeading"]))
    primary_code = analysis.get("recommended_primary_offence")
    matches = analysis.get("matches", [])
    likely = [m for m in matches if m["verdict"] in ("likely_applies", "possible_but_unclear")]
    if not likely:
        story.append(Paragraph(
            "Based on the facts provided, the applicable section could not be confidently determined. "
            "Please treat this document as a factual statement and let the investigating officer determine "
            "the appropriate provisions.", styles["Body"]))
    for m in likely:
        off = OFFENCE_BY_CODE.get(m["offence_code"])
        if not off:
            continue
        tag = " (most applicable)" if m["offence_code"] == primary_code else ""
        story.append(Paragraph(f"<b>{off['section']} — {off['title']}{tag}</b>", styles["Body"]))
        story.append(Paragraph(f"(Formerly {off['old_ipc']} under the earlier Indian Penal Code.)", styles["Small"]))
        story.append(Paragraph(m.get("overall_reasoning", ""), styles["Body"]))
        story.append(Paragraph(
            f"Classification: {'Cognizable' if off['cognizable'] else 'Non-cognizable'}, "
            f"{'Bailable' if off['bailable'] else 'Non-bailable'}. "
            f"Punishment: {off['punishment']}", styles["Small"]))
        story.append(Spacer(1, 4))

    any_cognizable = any(
        OFFENCE_BY_CODE.get(m["offence_code"], {}).get("cognizable")
        for m in likely
    )
    story.append(Paragraph("Procedural note (BNSS, 2023)", styles["SectionHeading"]))
    if any_cognizable:
        proc = BNSS_PROCEDURE["cognizable_offence"]
        story.append(Paragraph(proc["summary"], styles["Body"]))
        story.append(Paragraph(proc["zero_fir"], styles["Body"]))
        story.append(Paragraph(
            "If this station declines to register the FIR, Section 173(4) BNSS permits the complainant "
            "to send this complaint in writing to the Superintendent of Police.", styles["Body"]))
    else:
        proc = BNSS_PROCEDURE["non_cognizable_offence"]
        story.append(Paragraph(proc["summary"], styles["Body"]))
        story.append(Paragraph(proc["route"], styles["Body"]))

    if facts.get("evidence_mentioned"):
        story.append(Paragraph("Evidence enclosed / available", styles["SectionHeading"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(e, styles["Body"])) for e in facts["evidence_mentioned"]],
            bulletType="bullet",
        ))

    if facts.get("witnesses_mentioned"):
        story.append(Paragraph("Witnesses", styles["SectionHeading"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(w, styles["Body"])) for w in facts["witnesses_mentioned"]],
            bulletType="bullet",
        ))

    story.append(Paragraph("Prayer", styles["SectionHeading"]))
    story.append(Paragraph(
        "I therefore request that this complaint be registered and appropriate legal action be taken "
        "against the accused under the applicable provisions of law. I am willing to cooperate fully with "
        "the investigation and provide any further information or evidence as required.", styles["Body"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Signature: _______________________", styles["Body"]))
    story.append(Paragraph(f"Name: {facts.get('complainant_name') or '[Complainant Name]'}", styles["Body"]))
    story.append(Paragraph("Contact number: _______________________", styles["Body"]))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#CCCCCC"), thickness=0.5))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Disclaimer: This document was generated by NyayaLekh, an AI-assisted complaint drafting tool. "
        "It structures the facts as narrated by the complainant and suggests indicative legal provisions "
        "for reference only. It is NOT legal advice, and the sections cited are not binding on the police "
        "or any court. Please verify all details and applicable sections with the police station or a "
        "qualified advocate before relying on this document.", styles["Small"]))
    story.append(Paragraph(f"Document prepared for: {language_label} | Generated on {datetime.now().strftime('%d %B %Y, %H:%M')}",
                            styles["Small"]))

    doc.build(story)
    return buf.getvalue()
