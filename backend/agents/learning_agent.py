"""
Response Learning Agent
-----------------------
Implements the closed-loop feedback mechanism for NeuroLead.

When a prospect responds (replied / demoed / bounced / unsubscribed),
this agent:
  1. Records the response signal
  2. Adjusts scoring weight multipliers based on what worked
  3. Re-ranks affected leads
  4. Returns updated scores

Weight deltas are in-memory (per session). Persist to DB for production use.
"""

from typing import Optional
from collections import defaultdict
import math
from agents.scoring_engine import compute_score


# In-memory weight adjustments (additive deltas applied to base weights)
_weight_adjustments: dict[str, float] = {
    "icp_fit": 0.0,
    "intent_signals": 0.0,
    "trigger_signals": 0.0,
    "seniority_score": 0.0,
}

# Response signal registry: lead_id → list of signals
_response_log: dict[str, list[str]] = defaultdict(list)

# Base model weights (must mirror scoring_engine.py)
BASE_WEIGHTS = {
    "icp_fit": 0.35,
    "intent_signals": 0.30,
    "trigger_signals": 0.20,
    "seniority_score": 0.15,
}

RESPONSE_WEIGHT_UPDATES = {
    "replied": {
        "intent_signals": +0.02,
        "seniority_score": +0.01,
    },
    "demoed": {
        "icp_fit": +0.03,
        "intent_signals": +0.02,
        "seniority_score": +0.02,
    },
    "opened": {
        "intent_signals": +0.005,
    },
    "bounced": {
        "icp_fit": -0.01,
    },
    "unsubscribed": {
        "icp_fit": -0.02,
        "intent_signals": -0.01,
    },
}

MAX_DELTA = 0.15   # cap per-dimension adjustment to prevent runaway


def record_response(lead_id: str, response_type: str) -> dict:
    """
    Record a prospect response and update scoring weight adjustments.
    
    response_type: 'replied' | 'demoed' | 'opened' | 'bounced' | 'unsubscribed'
    """
    valid = set(RESPONSE_WEIGHT_UPDATES.keys())
    if response_type not in valid:
        return {"error": f"Unknown response type. Valid types: {sorted(valid)}"}

    _response_log[lead_id].append(response_type)

    updates = RESPONSE_WEIGHT_UPDATES.get(response_type, {})
    deltas_applied = {}
    for dim, delta in updates.items():
        new_val = _weight_adjustments[dim] + delta
        _weight_adjustments[dim] = max(-MAX_DELTA, min(MAX_DELTA, new_val))
        deltas_applied[dim] = delta

    return {
        "lead_id": lead_id,
        "response_recorded": response_type,
        "weight_deltas_applied": deltas_applied,
        "current_adjusted_weights": get_effective_weights(),
    }


def get_effective_weights() -> dict:
    """Return base weights + current adjustments, normalised to sum to 1."""
    raw = {k: BASE_WEIGHTS[k] + _weight_adjustments[k] for k in BASE_WEIGHTS}
    # Clamp negatives
    raw = {k: max(0.01, v) for k, v in raw.items()}
    total = sum(raw.values())
    return {k: round(v / total, 4) for k, v in raw.items()}


def recompute_score(lead: dict) -> dict:
    """
    Re-score a lead using the current adjusted weights.
    Applies dynamic weight multipliers on top of base scoring.
    """
    base_result = compute_score(lead)
    effective = get_effective_weights()

    # Recompute composite with adjusted weights
    comps = base_result["components"]
    composite = (
        effective["icp_fit"] * comps["icp_fit"] / 100
        + effective["intent_signals"] * comps["intent_signals"] / 100
        + effective["trigger_signals"] * comps["trigger_signals"] / 100
        + effective["seniority_score"] * comps["seniority_score"] / 100
    )
    score = round(composite * 100)
    score = max(0, min(100, score))

    if score >= 80:
        tier = "Hot"
    elif score >= 60:
        tier = "Warm"
    else:
        tier = "Cold"

    return {
        **base_result,
        "score": score,
        "tier": tier,
        "adjusted_weights_used": effective,
        "weight_adjustments": dict(_weight_adjustments),
        "recomputed": True,
    }


def rerank_leads(leads: list[dict]) -> list[dict]:
    """Re-score and re-rank all leads using current adjusted weights."""
    rescored = []
    for lead in leads:
        new_score = recompute_score(lead)
        rescored.append({**lead, "ml_score": new_score})
    rescored.sort(key=lambda x: x["ml_score"]["score"], reverse=True)
    return rescored


def get_learning_stats() -> dict:
    """Return current state of the learning agent."""
    total_signals = sum(len(v) for v in _response_log.values())
    signal_counts = defaultdict(int)
    for signals in _response_log.values():
        for s in signals:
            signal_counts[s] += 1

    return {
        "total_leads_with_responses": len(_response_log),
        "total_response_signals": total_signals,
        "signal_breakdown": dict(signal_counts),
        "current_weight_adjustments": dict(_weight_adjustments),
        "effective_weights": get_effective_weights(),
        "base_weights": BASE_WEIGHTS,
        "learning_active": total_signals > 0,
    }


def reset_learning() -> dict:
    """Reset all learning state (use with caution)."""
    global _weight_adjustments, _response_log
    _weight_adjustments = {k: 0.0 for k in BASE_WEIGHTS}
    _response_log = defaultdict(list)
    return {"status": "reset", "weights": BASE_WEIGHTS}
