"""
A/B Testing Agent
-----------------
Tracks outreach variant performance per lead segment and computes
winning variants based on open/reply/demo signal rates.

Uses CSV engagement columns as historical baseline:
  - Email Sent, Email Open, Email Bounced, Replied, Demoed
"""

from collections import defaultdict
from typing import Optional


def _engagement_score(lead: dict) -> float:
    """Compute 0–1 engagement score from known CSV signals."""
    score = 0.0
    if lead.get("email_open"):
        score += 0.20
    if lead.get("replied"):
        score += 0.50
    if lead.get("demoed"):
        score += 1.00
    if lead.get("email_bounced"):
        score -= 0.30
    return max(0.0, min(score, 1.0))


def analyse_ab_performance(leads: list[dict]) -> dict:
    """
    Aggregate engagement stats across all leads to determine
    best-performing variant patterns.

    Returns overall stats and per-segment analysis.
    """
    total = len(leads)
    sent = sum(1 for l in leads if l.get("email_sent"))
    opened = sum(1 for l in leads if l.get("email_open"))
    bounced = sum(1 for l in leads if l.get("email_bounced"))
    replied = sum(1 for l in leads if l.get("replied"))
    demoed = sum(1 for l in leads if l.get("demoed"))

    def rate(n: int) -> float:
        return round((n / sent * 100), 2) if sent > 0 else 0.0

    overall = {
        "total_leads": total,
        "emails_sent": sent,
        "open_rate_pct": rate(opened),
        "bounce_rate_pct": rate(bounced),
        "reply_rate_pct": rate(replied),
        "demo_rate_pct": rate(demoed),
    }

    # By tier
    tier_stats = defaultdict(lambda: {"sent": 0, "opened": 0, "replied": 0, "demoed": 0})
    for lead in leads:
        tier = (lead.get("lead_tier_csv") or lead.get("lead_tier_classification") or "Unknown").strip()
        if lead.get("email_sent"):
            tier_stats[tier]["sent"] += 1
        if lead.get("email_open"):
            tier_stats[tier]["opened"] += 1
        if lead.get("replied"):
            tier_stats[tier]["replied"] += 1
        if lead.get("demoed"):
            tier_stats[tier]["demoed"] += 1

    tier_breakdown = {}
    for tier, stats in tier_stats.items():
        s = stats["sent"]
        tier_breakdown[tier] = {
            "sent": s,
            "open_rate_pct": round(stats["opened"] / s * 100, 2) if s > 0 else 0,
            "reply_rate_pct": round(stats["replied"] / s * 100, 2) if s > 0 else 0,
            "demo_rate_pct": round(stats["demoed"] / s * 100, 2) if s > 0 else 0,
        }

    # By seniority
    seniority_stats = defaultdict(lambda: {"sent": 0, "replied": 0})
    for lead in leads:
        sen = lead.get("seniority", "Unknown").strip()
        if lead.get("email_sent"):
            seniority_stats[sen]["sent"] += 1
        if lead.get("replied"):
            seniority_stats[sen]["replied"] += 1

    seniority_breakdown = {
        sen: {
            "sent": s["sent"],
            "reply_rate_pct": round(s["replied"] / s["sent"] * 100, 2) if s["sent"] > 0 else 0,
        }
        for sen, s in seniority_stats.items()
    }

    # Winning variant recommendation
    winner = _pick_winner(tier_breakdown)

    return {
        "overall": overall,
        "by_tier": tier_breakdown,
        "by_seniority": seniority_breakdown,
        "winning_recommendation": winner,
    }


def _pick_winner(tier_breakdown: dict) -> dict:
    """
    Based on tier performance, recommend which outreach approach to double down on.
    """
    best_tier = None
    best_reply = -1.0
    for tier, stats in tier_breakdown.items():
        if stats.get("reply_rate_pct", 0) > best_reply:
            best_reply = stats["reply_rate_pct"]
            best_tier = tier

    return {
        "best_performing_tier": best_tier,
        "best_reply_rate_pct": best_reply,
        "recommendation": (
            f"Focus outreach on {best_tier} leads – "
            f"{best_reply:.1f}% reply rate. "
            f"Use Variant A (shorter, role-specific hook) for C-Suite; "
            f"Variant B (problem-led) for VP/Director."
        ),
    }


# In-memory A/B test registry (per-run state)
_ab_registry: dict[str, dict] = {}


def register_ab_send(lead_id: str, channel: str, variant: str) -> None:
    """Record that a specific variant was sent to a lead."""
    _ab_registry[lead_id] = {
        "lead_id": lead_id,
        "channel": channel,
        "variant": variant,
        "status": "sent",
        "response": None,
    }


def record_response(lead_id: str, response_type: str) -> dict:
    """
    Record a response event for a lead.
    response_type: 'opened' | 'replied' | 'bounced' | 'demoed' | 'unsubscribed'
    """
    if lead_id not in _ab_registry:
        _ab_registry[lead_id] = {"lead_id": lead_id, "status": "unknown", "response": None}
    _ab_registry[lead_id]["response"] = response_type
    _ab_registry[lead_id]["status"] = "responded"
    return _ab_registry[lead_id]


def get_ab_summary() -> dict:
    """Return current A/B registry summary."""
    total = len(_ab_registry)
    by_variant = defaultdict(lambda: {"sent": 0, "responses": 0})
    for entry in _ab_registry.values():
        v = entry.get("variant", "unknown")
        by_variant[v]["sent"] += 1
        if entry.get("response"):
            by_variant[v]["responses"] += 1

    return {
        "total_tracked": total,
        "by_variant": dict(by_variant),
    }
