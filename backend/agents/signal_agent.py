"""
Signal Discovery Agent
----------------------
Extracts and categorises intent / trigger signals from lead data.
In production this would call Apollo / LinkedIn / Crunchbase APIs.
With only CSV data it extracts rich signals from the enriched columns.
"""

from typing import Optional
import re
from datetime import datetime, timezone


FUNDING_KEYWORDS = [
    "series a", "series b", "series c", "series d",
    "seed", "pre-seed", "ipo", "private equity",
    "merger", "acquisition",
]

AI_TECH_KEYWORDS = [
    "ai", "machine learning", "llm", "gpt", "openai", "generative",
    "tensorflow", "pytorch", "hugging face", "vector", "embedding",
    "langchain", "rag", "chatgpt", "claude", "gemini",
]

DEVOPS_KEYWORDS = [
    "kubernetes", "docker", "terraform", "github actions", "argocd",
    "jenkins", "circleci", "gitlab", "argo", "helm", "tekton",
    "datadog", "grafana", "prometheus", "opentelemetry", "jaeger",
]

CLOUD_KEYWORDS = [
    "aws", "amazon", "azure", "google cloud", "gcp",
    "cloudflare", "digitalocean", "heroku", "vercel",
]

MODERN_FRONTEND = [
    "react", "next.js", "vue", "angular", "svelte", "typescript",
    "tailwind", "graphql", "rest api",
]


def _extract_tech_signals(technologies: str) -> dict:
    tech_lower = technologies.lower()
    return {
        "ai_ml": any(kw in tech_lower for kw in AI_TECH_KEYWORDS),
        "devops": any(kw in tech_lower for kw in DEVOPS_KEYWORDS),
        "cloud": any(kw in tech_lower for kw in CLOUD_KEYWORDS),
        "modern_frontend": any(kw in tech_lower for kw in MODERN_FRONTEND),
        "detected_tools": [
            kw for kw in AI_TECH_KEYWORDS + DEVOPS_KEYWORDS + CLOUD_KEYWORDS + MODERN_FRONTEND
            if kw in tech_lower
        ][:10],  # top 10
    }


def _extract_funding_signal(lead: dict) -> dict:
    funding_stage = lead.get("latest_funding", "").lower().strip()
    amount = lead.get("latest_funding_amount")
    raised_at = lead.get("last_raised_at", "")
    recent = lead.get("recent_funding", "").lower().strip() in ("yes", "yes ")
    total = lead.get("total_funding")

    # Parse recency
    months_since = None
    if raised_at:
        try:
            dt = datetime.fromisoformat(raised_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            months_since = round((now - dt).days / 30)
        except (ValueError, TypeError):
            pass

    stage_found = next((s for s in FUNDING_KEYWORDS if s in funding_stage), None)

    return {
        "has_funding": bool(stage_found or amount or recent),
        "stage": stage_found,
        "amount_usd": amount,
        "total_funding_usd": total,
        "raised_months_ago": months_since,
        "is_recent": recent or (months_since is not None and months_since <= 18),
    }


def _extract_seniority_signal(lead: dict) -> dict:
    title = lead.get("title", "").lower()
    seniority = lead.get("seniority", "").lower()
    departments = lead.get("departments", "").lower()

    is_technical = any(
        kw in title or kw in departments
        for kw in ["engineering", "technology", "technical", "platform", "infrastructure", "devops"]
    )
    is_decision_maker = any(
        kw in title or kw in seniority
        for kw in ["cto", "ceo", "vp", "chief", "founder", "director", "head of", "president"]
    )

    return {
        "is_technical_buyer": is_technical,
        "is_decision_maker": is_decision_maker,
        "role_type": "technical_dm" if (is_technical and is_decision_maker)
                     else ("dm" if is_decision_maker else ("technical" if is_technical else "other")),
    }


def _extract_company_signals(lead: dict) -> dict:
    employees = lead.get("employees") or 0
    revenue = lead.get("annual_revenue") or 0

    if employees >= 1000:
        size_band = "enterprise"
    elif employees >= 200:
        size_band = "mid-market"
    elif employees >= 50:
        size_band = "smb"
    else:
        size_band = "startup"

    return {
        "employee_count": employees,
        "size_band": size_band,
        "annual_revenue_usd": revenue,
        "country": lead.get("country", ""),
    }


def _engagement_signals(lead: dict) -> dict:
    return {
        "email_sent": lead.get("email_sent", False),
        "email_opened": lead.get("email_open", False),
        "replied": lead.get("replied", False),
        "demoed": lead.get("demoed", False),
        "email_status": lead.get("email_status", ""),
    }


def discover_signals(lead: dict) -> dict:
    """
    Main entry: discover all signals for a lead.
    Returns structured signal dict with confidence scores.
    """
    tech_signals = _extract_tech_signals(lead.get("technologies", ""))
    funding_signal = _extract_funding_signal(lead)
    seniority_signal = _extract_seniority_signal(lead)
    company_signal = _extract_company_signals(lead)
    engagement = _engagement_signals(lead)

    # Aggregate confidence score (0–100)
    confidence = 40  # base
    if funding_signal["is_recent"]:
        confidence += 20
    if seniority_signal["is_decision_maker"]:
        confidence += 15
    if tech_signals["ai_ml"] or tech_signals["devops"]:
        confidence += 10
    if engagement["replied"] or engagement["demoed"]:
        confidence += 15
    if company_signal["size_band"] in ("enterprise", "mid-market"):
        confidence += 10
    confidence = min(confidence, 100)

    return {
        "lead_id": lead.get("id"),
        "source": "csv_fallback",  # would be "apollo" / "clay" with live APIs
        "confidence": confidence,
        "signals": {
            "technology": tech_signals,
            "funding": funding_signal,
            "seniority": seniority_signal,
            "company": company_signal,
            "engagement": engagement,
        },
        "summary": _build_summary(lead, tech_signals, funding_signal, seniority_signal),
    }


def _build_summary(lead, tech, funding, seniority) -> str:
    parts = []
    name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
    company = lead.get("company", "")
    title = lead.get("title", "")
    if name:
        parts.append(f"{name} ({title}) at {company}")
    if funding["is_recent"] and funding["stage"]:
        parts.append(f"raised {funding['stage'].title()} recently")
    if seniority["is_decision_maker"]:
        parts.append("decision-maker")
    if tech["ai_ml"]:
        parts.append("uses AI/ML stack")
    if tech["devops"]:
        parts.append("DevOps-mature")
    return " · ".join(parts) if parts else "No summary"


def discover_signals_batch(leads: list[dict]) -> list[dict]:
    """Run signal discovery over all leads."""
    return [discover_signals(lead) for lead in leads]
