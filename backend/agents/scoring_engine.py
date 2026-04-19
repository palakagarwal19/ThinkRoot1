"""
ML Lead Scoring Engine
----------------------
Computes a composite lead score (0-100) from CSV features and classifies
each lead as Hot / Warm / Cold.

Score formula (mirrors NeuroLead architecture doc):
  Score = 0.35 * icp_fit
        + 0.30 * intent_signals
        + 0.20 * trigger_signals
        + 0.15 * seniority_score

All sub-scores are normalised to [0, 1] before weighting.
"""

import re
from typing import Optional

# ── Seniority mapping ────────────────────────────────────────────────────────
SENIORITY_SCORES = {
    "founder": 1.0,
    "owner": 1.0,
    "c suite": 1.0,
    "c-suite": 1.0,
    "vp": 0.80,
    "partner": 0.75,
    "director": 0.60,
    "manager": 0.40,
    "senior": 0.30,
    "individual contributor": 0.20,
    "entry": 0.10,
}

TITLE_BOOSTS = {
    "cto": 0.20,
    "chief technology": 0.20,
    "vp engineering": 0.15,
    "vp of engineering": 0.15,
    "head of engineering": 0.15,
    "svp": 0.12,
    "evp": 0.12,
    "director of engineering": 0.10,
    "director of platform": 0.10,
    "head of platform": 0.10,
    "chief product": 0.10,
    "cpo": 0.10,
    "ceo": 0.08,
    "co-founder": 0.08,
    "cofounder": 0.08,
}

# ICP industry keywords (P95.ai context: enterprise software, SaaS, IT services)
ICP_INDUSTRIES = {
    "information technology", "software", "saas", "cloud computing",
    "enterprise software", "fintech", "cybersecurity", "ai", "devops",
    "data", "machine learning", "technology", "internet", "automation",
}

MODERN_TECH_SIGNALS = {
    "kubernetes", "docker", "terraform", "react", "next.js", "fastapi",
    "graphql", "kafka", "aws", "azure", "gcp", "github actions", "argocd",
    "datadog", "snowflake", "dbt", "python", "go+", "rust",
}

FUNDING_STAGES_RANK = {
    "series c": 1.0, "series d": 1.0, "series e": 1.0,
    "series b": 0.85, "series a": 0.70,
    "seed": 0.50, "pre-seed": 0.40,
    "private equity": 0.90, "merger / acquisition": 0.80, "ipo": 0.95,
    "other": 0.30,
}


def _score_icp_fit(lead: dict) -> float:
    """[0-1] How well the lead fits P95.ai's ICP."""
    score = 0.0

    # Hard signal from Apollo enrichment
    icp_match = lead.get("icp_match", "").lower().strip()
    if icp_match in ("yes", "yes "):
        score += 0.60

    # Industry keyword match
    industry = lead.get("industry", "").lower()
    if any(kw in industry for kw in ICP_INDUSTRIES):
        score += 0.25

    # Company size (sweet spot: 50-5000 employees for enterprise)
    employees = lead.get("employees") or 0
    if 50 <= employees <= 5000:
        score += 0.15
    elif employees > 5000:
        score += 0.08

    return min(score, 1.0)


def _score_intent_signals(lead: dict) -> float:
    """[0-1] Intent / behavioural buying signals."""
    score = 0.0

    # Modern tech stack
    modern_stack = lead.get("modern_stack", "").lower().strip()
    if modern_stack in ("yes", "yes "):
        score += 0.40

    # Tech stack keyword overlap
    tech = lead.get("technologies", "").lower()
    matches = sum(1 for kw in MODERN_TECH_SIGNALS if kw in tech)
    score += min(matches * 0.05, 0.30)

    # Keywords from Apollo (interest signals)
    keywords = lead.get("keywords", "").lower()
    ai_signals = sum(1 for kw in ["ai", "machine learning", "llm", "generative", "automation"] if kw in keywords)
    score += min(ai_signals * 0.06, 0.20)

    # Email engagement history from CSV
    if lead.get("email_open"):
        score += 0.05
    if lead.get("replied"):
        score += 0.10
    if lead.get("demoed"):
        score += 0.15

    return min(score, 1.0)


def _score_trigger_signals(lead: dict) -> float:
    """[0-1] External trigger events (funding, hiring, news)."""
    score = 0.0

    # Recent funding flag from Apollo
    recent_funding = lead.get("recent_funding", "").lower().strip()
    if recent_funding in ("yes", "yes "):
        score += 0.50

    # Funding stage
    latest = lead.get("latest_funding", "").lower().strip()
    for stage, rank_score in FUNDING_STAGES_RANK.items():
        if stage in latest:
            score += rank_score * 0.30
            break

    # Funding amount (>$5M is a strong signal)
    amount = lead.get("latest_funding_amount") or 0
    if amount >= 50_000_000:
        score += 0.20
    elif amount >= 10_000_000:
        score += 0.15
    elif amount >= 5_000_000:
        score += 0.10
    elif amount >= 1_000_000:
        score += 0.05

    return min(score, 1.0)


def _score_seniority(lead: dict) -> float:
    """[0-1] Decision-maker seniority score."""
    seniority = lead.get("seniority", "").lower().strip()
    title = lead.get("title", "").lower().strip()

    base = 0.0
    for level, level_score in SENIORITY_SCORES.items():
        if level in seniority:
            base = level_score
            break

    # Title boost
    boost = 0.0
    for kw, kw_boost in TITLE_BOOSTS.items():
        if kw in title:
            boost = max(boost, kw_boost)

    return min(base + boost, 1.0)


def compute_score(lead: dict) -> dict:
    """
    Compute NeuroLead composite score for a single lead.

    Returns a dict with:
      - score (int 0-100)
      - tier ('Hot' | 'Warm' | 'Cold')
      - components (individual sub-scores)
      - reasoning (human-readable explanation)
    """
    icp_fit = _score_icp_fit(lead)
    intent = _score_intent_signals(lead)
    trigger = _score_trigger_signals(lead)
    seniority = _score_seniority(lead)

    # Weighted composite (matches NeuroLead formula)
    composite = (
        0.35 * icp_fit
        + 0.30 * intent
        + 0.20 * trigger
        + 0.15 * seniority
    )
    score = round(composite * 100)

    # Override with CSV tier if available and score differs significantly
    csv_score = lead.get("lead_score_csv")
    if csv_score is not None:
        # Blend: 70% ML + 30% Apollo-provided score
        score = round(0.70 * score + 0.30 * csv_score)

    score = max(0, min(100, score))

    # Classification
    if score >= 80:
        tier = "Hot"
    elif score >= 60:
        tier = "Warm"
    else:
        tier = "Cold"

    # Build reasoning
    reasons = []
    if icp_fit >= 0.60:
        reasons.append(f"Strong ICP fit ({lead.get('industry', 'N/A')})")
    if intent >= 0.50:
        reasons.append("Modern tech stack + active intent signals")
    if trigger >= 0.40:
        reasons.append(f"Recent funding trigger ({lead.get('latest_funding', 'N/A')})")
    if seniority >= 0.75:
        reasons.append(f"Senior decision-maker ({lead.get('title', 'N/A')})")
    if lead.get("replied"):
        reasons.append("Previously replied to outreach")
    if lead.get("demoed"):
        reasons.append("Demo completed")

    if not reasons:
        reasons.append("Standard qualification – nurture recommended")

    return {
        "score": score,
        "tier": tier,
        "components": {
            "icp_fit": round(icp_fit * 100, 1),
            "intent_signals": round(intent * 100, 1),
            "trigger_signals": round(trigger * 100, 1),
            "seniority_score": round(seniority * 100, 1),
        },
        "weights": {
            "icp_fit": 0.35,
            "intent_signals": 0.30,
            "trigger_signals": 0.20,
            "seniority_score": 0.15,
        },
        "reasoning": reasons,
    }


def score_all_leads(leads: list[dict]) -> list[dict]:
    """Attach `ml_score` dict to each lead and return enriched list."""
    scored = []
    for lead in leads:
        result = compute_score(lead)
        enriched = {**lead, "ml_score": result}
        scored.append(enriched)
    # Sort by score descending
    scored.sort(key=lambda x: x["ml_score"]["score"], reverse=True)
    return scored
