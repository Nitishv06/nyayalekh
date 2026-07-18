"""
bns_data.py
Structured, verified data on 4 high-frequency BNS offences + BNSS FIR procedure.

IMPORTANT: This data was verified against multiple independent legal sources
in July 2026 (post BNS/BNSS commencement of 1 July 2024). Section numbers and
classifications (cognizable/bailable) are the load-bearing facts of this app —
if you change or add offences, re-verify against the bare act / a current
legal reference before shipping. Do NOT let an LLM invent section numbers.

Each offence entry has:
  - code: internal id used across the app
  - section: BNS section (with sub-section where the classification differs
    by sub-section, e.g. cheating's basic vs aggravated forms)
  - title: plain title
  - old_ipc: the IPC section it replaced (for the "you may know this as..." UX)
  - ingredients: list of legal elements the AI checks the narrative against
  - cognizable / bailable / triable_by / punishment: classification
  - explanation: plain-language one-liner for a non-lawyer
"""

OFFENCES = [
    {
        "code": "cheating",
        "section": "BNS Section 318(4)",
        "title": "Cheating and dishonestly inducing delivery of property",
        "old_ipc": "IPC Section 420 (also draws on old 415/417/418)",
        "ingredients": [
            "The accused deceived the complainant (made a false representation, promise, or dishonest concealment of a fact).",
            "The deception caused the complainant to deliver property, money, or a valuable security, OR to do/omit an act they would not otherwise have done.",
            "The accused acted fraudulently or dishonestly at the time of making the representation (not merely a later failure to honour a genuine promise).",
        ],
        "distinguish_from": "A simple business/contract dispute or loan default where the promise was genuine at the time it was made is a CIVIL matter, not cheating. Courts have repeatedly cautioned against converting bona fide contractual disputes into criminal cases (dishonest intent must exist from the start).",
        "cognizable": True,
        "bailable": False,
        "triable_by": "Magistrate of the First Class",
        "punishment": "Up to 7 years imprisonment and fine (up to 3 years for basic cheating under 318(2); enhanced under 318(3)/(4) for breach of trust or property inducement).",
        "explanation": "Someone tricked you into handing over money or property using a false promise or lie made with dishonest intent from the start.",
    },
    {
        "code": "theft",
        "section": "BNS Section 303",
        "title": "Theft",
        "old_ipc": "IPC Sections 378 / 379",
        "ingredients": [
            "The property taken is movable property.",
            "It was in the complainant's possession.",
            "The accused took it without the complainant's consent.",
            "The accused intended to take it dishonestly (permanently deprive the owner), and moved the property in order to take it.",
        ],
        "distinguish_from": "If the property was handed over voluntarily and then not returned, that may be criminal breach of trust or cheating, not theft. If force or threat of force was used at the time of taking, consider robbery instead.",
        "cognizable": True,
        "bailable": True,
        "triable_by": "Any Magistrate",
        "punishment": "Up to 3 years imprisonment or fine or both; up to 5 years (rigorous) on a second or subsequent conviction. First-time theft of property under Rs. 5,000, if returned, may attract community service instead of jail.",
        "explanation": "Someone dishonestly took your movable property (phone, bag, vehicle, cash) without your consent.",
    },
    {
        "code": "criminal_intimidation",
        "section": "BNS Section 351",
        "title": "Criminal intimidation",
        "old_ipc": "IPC Sections 503 / 506 / 507 / 508",
        "ingredients": [
            "The accused threatened the complainant with injury to body, reputation, or property (or to a person the complainant is interested in).",
            "The threat was made with intent to cause alarm to the complainant, OR to cause the complainant to do an act they are not legally bound to do, OR to omit an act they are legally entitled to do (as a means of avoiding the threat being carried out).",
        ],
        "distinguish_from": "Vague rudeness, a heated argument, or a one-off angry remark without a clear threat of injury usually does not meet the bar. The threat must be specific enough to cause a reasonable person alarm.",
        "cognizable": False,
        "bailable": True,
        "triable_by": "Any Magistrate (basic form); Sessions Court for the aggravated form (threat of death or grievous hurt, anonymous threat)",
        "punishment": "Up to 2 years imprisonment or fine or both for the basic offence; up to 7 years for a threat of death or grievous hurt (351(2)/(3)). Classification of the aggravated form as cognizable/non-bailable varies — flagged for the user to confirm at the station.",
        "explanation": "Someone threatened to hurt you, your reputation, or your property to frighten you or force you to act (or not act) against your will.",
    },
    {
        "code": "voluntarily_causing_hurt",
        "section": "BNS Section 115(2)",
        "title": "Voluntarily causing hurt",
        "old_ipc": "IPC Section 323 (also draws on old 321)",
        "ingredients": [
            "The accused caused bodily pain, disease, or infirmity to the complainant.",
            "The act was done voluntarily — either with intent to cause hurt, or with knowledge that the act was likely to cause hurt.",
            "The hurt is 'simple' — not grievous (no fracture, permanent damage, danger to life, etc. — if any of these are present, this is likely grievous hurt under a different, more serious section and the user should be told to flag this explicitly).",
        ],
        "distinguish_from": "If the injury involves a fracture, loss of a limb/sense, danger to life, or disfigurement, this is grievous hurt (a more serious, separate offence) — the app should flag this for escalation rather than classify it as simple hurt.",
        "cognizable": False,
        "bailable": True,
        "triable_by": "Any Magistrate",
        "punishment": "Up to 1 year imprisonment or fine up to Rs. 10,000, or both.",
        "explanation": "Someone deliberately caused you physical pain or minor injury — a slap, a scuffle, a scratch — without a weapon and without serious injury.",
    },
]

BNSS_PROCEDURE = {
    "cognizable_offence": {
        "summary": "For a cognizable offence, the police MUST register an FIR on receiving information — they cannot refuse to register it or ask you to 'go elsewhere' first, and no prior permission from a magistrate is needed for them to start investigating.",
        "zero_fir": "Under BNSS Section 173(1), you can report a cognizable offence at ANY police station regardless of where the crime happened ('Zero FIR') — the station cannot turn you away for jurisdiction reasons. It is registered with a serial number '0' and transferred to the police station with territorial jurisdiction.",
        "e_fir": "Information can also be given electronically; if given electronically, it must be signed by the informant within 3 days (BNSS Section 173(1)(ii)).",
        "refusal_remedy": "If the officer-in-charge refuses to register your FIR, BNSS Section 173(4) lets you send the information in writing (by post or otherwise) to the Superintendent of Police, who must either investigate it personally or direct an investigation if a cognizable offence is disclosed.",
        "free_copy": "You are entitled to a free copy of the FIR immediately after registration (BNSS Section 173(2)).",
    },
    "non_cognizable_offence": {
        "summary": "For a non-cognizable offence, the police cannot arrest without a warrant and cannot investigate without the permission of a Magistrate (BNSS Section 174, replacing old CrPC Section 155).",
        "route": "The police will record your complaint in the 'NC' (non-cognizable) register and issue you a copy/reference number, but will not investigate on their own. To get action, you (or your advocate) file a private complaint before a Magistrate under BNSS provisions for complaint cases, and the Magistrate can direct an investigation or take cognizance directly.",
        "practical_tip": "Many stations will still try to counsel/mediate a non-cognizable dispute informally. Always insist on a written NC entry or acknowledgment even if no FIR is registered — it's your documentary proof that you reported it.",
    },
}
