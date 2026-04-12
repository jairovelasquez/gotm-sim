import json
import random
from typing import Dict, List
from app.models import Decisions, KPIResult
from app.scenarios.default import SCENARIO

WEIGHTS = {
    "awareness": 0.24, "cac": 0.14, "conversion": 0.16,
    "sales": 0.18, "roas": 0.12, "marketShare": 0.08, "launchEfficiency": 0.08
}

def _normalize(kpi: str, value: float) -> float:
    norms = {
        "awareness": lambda v: min(100, max(0, (v - 10) / 90 * 100)),
        "cac": lambda v: min(100, max(0, (90 - v) / 70 * 100)),   # lower better
        "conversion": lambda v: min(100, max(0, (v - 0.5) / 5 * 100)),
        "sales": lambda v: min(100, max(0, (v - 30) / 200 * 100)),
        "roas": lambda v: min(100, max(0, (v - 0.5) / 4 * 100)),
        "marketShare": lambda v: min(100, max(0, (v - 1) / 9 * 100)),
        "launchEfficiency": lambda v: min(100, max(0, (v - 30) / 70 * 100)),
    }
    return norms.get(kpi, lambda v: v)(value)

def calculate_final_kpis(decisions: Decisions, strategy_tags: List[str]) -> Dict:
    base = SCENARIO["baseline_kpis"].copy()
    deltas = {k: 0.0 for k in base}

    # Pricing deltas
    if decisions.pricing == "premium":
        deltas["roas"] += 1.3; deltas["cac"] += 9; deltas["conversion"] -= 0.7
        deltas["sales"] -= 28; deltas["marketShare"] += 1.1
    elif decisions.pricing == "intro_offer":
        deltas["conversion"] += 1.4; deltas["sales"] += 48; deltas["roas"] -= 1.0
        deltas["cac"] -= 14; deltas["launchEfficiency"] -= 8
    elif decisions.pricing == "value_led":
        deltas["cac"] -= 18; deltas["sales"] += 35; deltas["conversion"] += 0.8
    # competitive = neutral

    # Segment deltas
    segment_map = {
        "genz_trend_seekers": {"awareness": 18, "conversion": 0.9, "marketShare": 1.2},
        "value_buyers": {"cac": -15, "sales": 40},
        "premium_lifestyle": {"roas": 1.1, "marketShare": 1.4},
        "early_adopters": {"awareness": 12, "launchEfficiency": 10}
    }
    for k, v in segment_map.get(decisions.priority_segment, {}).items():
        deltas[k] += v

    # Channel deltas
    channel_map = {
        "social_first": {"awareness": 16, "roas": -0.6},
        "influencer_led": {"roas": 0.9, "cac": 6, "marketShare": 0.8},
        "retail_activation": {"conversion": 1.1, "sales": 30, "awareness": -8},
        "balanced_mix": {"awareness": 6, "conversion": 0.6, "roas": 0.3}
    }
    for k, v in channel_map.get(decisions.channel_mix, {}).items():
        deltas[k] += v

    # Tiny strategy tag influence (deterministic)
    if any(t in ["social", "awareness", "genz"] for t in strategy_tags):
        deltas["awareness"] += 7

    # Apply
    final = {k: round(base[k] + deltas[k], 2) for k in base}
    # Clamp
    final["cac"] = max(22, min(82, final["cac"]))
    final["roas"] = max(0.8, min(5.5, final["roas"]))
    final["conversion"] = max(0.8, min(6.5, final["conversion"]))

    # Launch efficiency derived
    final["launchEfficiency"] = round((final["awareness"] * 0.3 + final["roas"] * 12 + final["conversion"] * 8 - final["cac"] * 0.4), 1)

    # Final score
    normed = {_k: _normalize(_k, final[_k]) for _k in final}
    score = sum(normed[k] * WEIGHTS[k] for k in WEIGHTS)
    final["final_score"] = round(score, 1)

    return final

def get_staged_updates(decisions: Decisions, strategy_tags: List[str], competitor_event: str) -> List[Dict]:
    """Pre-compute 4 stages for SSE playback"""
    final_kpis = calculate_final_kpis(decisions, strategy_tags)
    base = SCENARIO["baseline_kpis"]
    stages = []
    competitor = None

    # Competitor event selection (deterministic)
    event_map = {
        "social_first": ("Social Burst", "Rival brand floods TikTok with 3x budget."),
        "influencer_led": ("Influencer Noise", "Competitor signs 5 macro-influencers."),
        "retail_activation": ("Discount Push", "Competitor runs 40% off in-store."),
        "balanced_mix": ("Copycat Positioning", "Competitor launches near-identical beverage.")
    }
    event_name, event_desc = event_map.get(decisions.channel_mix, ("Competitor Pressure", "Market reacts to your launch."))
    competitor = {"event": event_name, "commentary": event_desc}

    for i in range(1, 5):
        progress = i / 4.0
        stage_kpis = {k: round(base[k] + (final_kpis[k] - base[k]) * progress, 2) for k in base}
        if i == 3:
            stage_kpis["awareness"] = round(stage_kpis["awareness"] * 0.95, 2)  # competitor dip

        narrative = [
            "Initial buzz building in urban Gen Z circles...",
            "Segment response stronger than expected...",
            f"Competitor {event_name.lower()} detected...",
            "Final consolidation – market share locked in."
        ][i-1]

        stages.append({
            "stage": i,
            "stage_name": ["Initial Reaction", "Segment Shift", "Competitor Response", "Final Consolidation"][i-1],
            "kpis": stage_kpis,
            "narrative": narrative,
            "competitor": competitor if i == 3 else None
        })
    stages[-1]["complete"] = True
    return stages
