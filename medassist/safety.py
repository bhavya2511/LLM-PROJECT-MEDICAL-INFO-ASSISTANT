"""Rule-based safety router: runs before retrieval/generation."""
import re

DISCLAIMER = ("Educational information only, not medical advice. It cannot diagnose or treat you. "
              "Talk to a qualified healthcare professional about your own health.")

EMERGENCY = re.compile(
    r"\b(chest pain|can'?t breathe|cannot breathe|difficulty breathing|having a stroke|overdos\w*|"
    r"suicid\w*|kill myself|self[- ]harm|severe bleeding|unconscious|anaphyla\w*|having a heart attack)\b",
    re.I)
PERSONAL_ADVICE = re.compile(
    r"\b(do i have|should i take|how much .* should i|what dose|dosage for me|diagnose me|"
    r"prescribe|can i stop taking|am i dying)\b", re.I)

EMERGENCY_MSG = ("If this is an emergency or you are in danger, call your local emergency number now "
                 "(112 in India, 911 in the US) or go to the nearest emergency room. If you are having "
                 "thoughts of self-harm, please contact a crisis line such as iCall (India: 9152987821) "
                 "or 988 (US).")
PERSONAL_MSG = ("I can't diagnose conditions or recommend personal treatment or doses. I can explain "
                "what a disease is, its causes, symptoms and general treatments from trusted sources. "
                "Please ask a doctor or pharmacist about your own situation.")


def check(question: str) -> dict:
    """Return {'allowed': bool, 'message': str|None, 'kind': str|None}."""
    if EMERGENCY.search(question):
        return {"allowed": False, "kind": "emergency", "message": EMERGENCY_MSG}
    if PERSONAL_ADVICE.search(question):
        return {"allowed": False, "kind": "personal", "message": PERSONAL_MSG}
    return {"allowed": True, "kind": None, "message": None}
