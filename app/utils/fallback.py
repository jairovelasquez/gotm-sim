"""
Deterministic fallback templates when Bedrock is unavailable
"""
from app.models import InterpretedStrategy

def fallback_interpret_strategy(text: str) -> dict:
    """Simple keyword-based fallback"""
    text_lower = text.lower()
    tags = []
    if any(word in text_lower for word in ["social", "tiktok", "instagram", "viral"]):
        tags.append("social")
    if any(word in text_lower for word in ["premium", "luxury", "high-end"]):
        tags.append("premium")
    if any(word in text_lower for word in ["genz", "young", "youth", "urban"]):
        tags.append("genz")
    if any(word in text_lower for word in ["value", "affordable", "budget"]):
        tags.append("value")
    if not tags:
        tags = ["awareness", "balanced"]

    return {
        "summary": "Creative go-to-market strategy focused on urban Gen Z channels.",
        "tags": tags,
        "alignment_score": 68
    }


def fallback_executive_summary(session_data: dict) -> str:
    score = session_data.get("final_score", 65)
    if score >= 82:
        verdict = "outstanding"
    elif score >= 70:
        verdict = "strong"
    elif score >= 55:
        verdict = "solid"
    else:
        verdict = "mixed"

    return f"""
    The VibeFuel launch delivered a {verdict} performance. 
    Your {session_data['decisions'].get('pricing', 'chosen')} pricing combined with 
    {session_data['decisions'].get('channel_mix', 'selected channels')} drove solid awareness 
    among urban Gen Z consumers, though some efficiency trade-offs appeared due to competitive pressure.
    Overall, this positions VibeFuel well for continued growth in the wellness beverage category.
    """.strip()