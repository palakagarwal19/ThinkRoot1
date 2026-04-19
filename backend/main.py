"""
NeuroLead – FastAPI Main Application
=====================================
Multi-agent AI lead intelligence system for P95.ai

Routes:
  GET  /                          Health check
  GET  /api/leads                 List leads (paginated, filtered)
  GET  /api/leads/stats           Aggregate stats
  GET  /api/leads/{id}            Single lead detail + ML score
  GET  /api/leads/{id}/signals    Signal discovery for a lead
  GET  /api/leads/{id}/score      ML score breakdown
  GET  /api/leads/{id}/outreach   Generate A/B outreach
  GET  /api/graph/{company}       Buying committee graph for a company
  GET  /api/graph                 All company graphs summary
  GET  /api/ab-testing            A/B performance stats
  POST /api/ab-testing/register   Register variant send
  POST /api/learn/response        Submit response signal
  GET  /api/learn/stats           Learning agent stats
  POST /api/learn/reset           Reset learning state
  GET  /api/pipeline              System pipeline status
"""

import os
import sys
from pathlib import Path
from typing import Optional
import asyncio

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ── Ensure local packages are importable ─────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from data.csv_loader import get_leads, get_lead_by_id
from agents.scoring_engine import compute_score, score_all_leads
from agents.signal_agent import discover_signals
from agents.enrichment_agent import enrich_lead_sync
from agents.graph_engine import get_buying_committee, get_all_committees
from agents.outreach_agent import generate_outreach
from agents.ab_agent import analyse_ab_performance, register_ab_send, record_response as ab_record, get_ab_summary
from agents.learning_agent import (
    record_response as learn_record,
    rerank_leads,
    get_learning_stats,
    reset_learning,
    get_effective_weights,
)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NeuroLead API",
    description="Multi-Agent AI Lead Intelligence System for P95.ai",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class ResponseSignal(BaseModel):
    lead_id: str
    response_type: str  # replied | demoed | opened | bounced | unsubscribed


class ABRegister(BaseModel):
    lead_id: str
    channel: str   # email | linkedin
    variant: str   # A | B


# ── Cache scored leads once per session ──────────────────────────────────────
_scored_cache: Optional[list[dict]] = None


def _get_scored() -> list[dict]:
    global _scored_cache
    if _scored_cache is None:
        raw = get_leads()
        _scored_cache = score_all_leads(raw)
    return _scored_cache


def _invalidate_cache():
    global _scored_cache
    _scored_cache = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health():
    leads = get_leads()
    return {
        "status": "online",
        "system": "NeuroLead",
        "version": "1.0.0",
        "total_leads_loaded": len(leads),
        "agents": [
            "SignalDiscoveryAgent",
            "EnrichmentAgent",
            "MLScoringEngine",
            "BuyingCommitteeGraphEngine",
            "LLMOutreachAgent",
            "ABTestingAgent",
            "ResponseLearningAgent",
        ],
        "data_source": "Apollo CSV + Clay/Apollo API fallback",
    }


# ── Leads ─────────────────────────────────────────────────────────────────────

@app.get("/api/leads", tags=["Leads"])
def list_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    tier: Optional[str] = Query(None, description="Hot | Warm | Cold"),
    industry: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None, description="Search name, company, email"),
    sort_by: str = Query("score", description="score | company | country"),
    order: str = Query("desc", description="asc | desc"),
):
    """Paginated, filterable lead list with ML scores."""
    leads = _get_scored()

    # Filters
    if tier:
        leads = [l for l in leads if l["ml_score"]["tier"].lower() == tier.lower()]
    if industry:
        leads = [l for l in leads if industry.lower() in l.get("industry", "").lower()]
    if country:
        leads = [l for l in leads if country.lower() in l.get("country", "").lower()]
    if min_score is not None:
        leads = [l for l in leads if l["ml_score"]["score"] >= min_score]
    if max_score is not None:
        leads = [l for l in leads if l["ml_score"]["score"] <= max_score]
    if search:
        q = search.lower()
        leads = [
            l for l in leads
            if q in l.get("company", "").lower()
            or q in (l.get("first_name", "") + " " + l.get("last_name", "")).lower()
            or q in l.get("email", "").lower()
        ]

    # Sort
    reverse = order.lower() == "desc"
    if sort_by == "score":
        leads = sorted(leads, key=lambda x: x["ml_score"]["score"], reverse=reverse)
    elif sort_by == "company":
        leads = sorted(leads, key=lambda x: x.get("company", ""), reverse=reverse)
    elif sort_by == "country":
        leads = sorted(leads, key=lambda x: x.get("country", ""), reverse=reverse)

    # Pagination
    total = len(leads)
    start = (page - 1) * limit
    page_data = leads[start : start + limit]

    # Strip heavy keyword fields for list view
    slim = []
    for l in page_data:
        slim.append({
            "id": l["id"],
            "name": f"{l.get('first_name','')} {l.get('last_name','')}".strip(),
            "title": l.get("title"),
            "company": l.get("company"),
            "email": l.get("email"),
            "email_status": l.get("email_status"),
            "seniority": l.get("seniority"),
            "industry": l.get("industry"),
            "country": l.get("country"),
            "employees": l.get("employees"),
            "linkedin_url": l.get("linkedin_url"),
            "website": l.get("website"),
            "latest_funding": l.get("latest_funding"),
            "annual_revenue": l.get("annual_revenue"),
            "icp_match": l.get("icp_match"),
            "modern_stack": l.get("modern_stack"),
            "recent_funding": l.get("recent_funding"),
            "ml_score": l["ml_score"],
            "email_sent": l.get("email_sent"),
            "email_open": l.get("email_open"),
            "replied": l.get("replied"),
            "demoed": l.get("demoed"),
        })

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, -(-total // limit)),
        "leads": slim,
    }


@app.get("/api/leads/stats", tags=["Leads"])
def leads_stats():
    """Aggregate stats: tier counts, top industries, country breakdown."""
    leads = _get_scored()

    from collections import Counter, defaultdict

    tier_counts = Counter(l["ml_score"]["tier"] for l in leads)
    industries = Counter(l.get("industry", "Unknown") for l in leads)
    countries = Counter(l.get("country", "Unknown") for l in leads)
    seniority = Counter(l.get("seniority", "Unknown") for l in leads)

    scores = [l["ml_score"]["score"] for l in leads]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    replied = sum(1 for l in leads if l.get("replied"))
    demoed = sum(1 for l in leads if l.get("demoed"))
    sent = sum(1 for l in leads if l.get("email_sent"))
    opened = sum(1 for l in leads if l.get("email_open"))

    return {
        "total_leads": len(leads),
        "tier_counts": dict(tier_counts),
        "average_ml_score": avg_score,
        "top_industries": dict(industries.most_common(10)),
        "top_countries": dict(countries.most_common(10)),
        "seniority_breakdown": dict(seniority.most_common()),
        "engagement": {
            "emails_sent": sent,
            "emails_opened": opened,
            "replied": replied,
            "demoed": demoed,
            "open_rate_pct": round(opened / sent * 100, 2) if sent else 0,
            "reply_rate_pct": round(replied / sent * 100, 2) if sent else 0,
        },
        "effective_weights": get_effective_weights(),
    }


@app.get("/api/leads/{lead_id}", tags=["Leads"])
def get_lead(lead_id: str):
    """Full lead detail including ML score, signals, and enrichment."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")

    score = compute_score(lead)
    signals = discover_signals(lead)
    enrichment = enrich_lead_sync(lead)

    return {
        "lead": lead,
        "ml_score": score,
        "signals": signals,
        "enrichment": enrichment,
    }


@app.get("/api/leads/{lead_id}/signals", tags=["Leads"])
def get_lead_signals(lead_id: str):
    """Signal discovery output for a single lead."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")
    return discover_signals(lead)


@app.get("/api/leads/{lead_id}/score", tags=["Leads"])
def get_lead_score(lead_id: str):
    """ML score breakdown (components + weights) for a single lead."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")
    return {
        "lead_id": lead_id,
        "name": f"{lead.get('first_name','')} {lead.get('last_name','')}".strip(),
        "company": lead.get("company"),
        **compute_score(lead),
    }


@app.get("/api/leads/{lead_id}/outreach", tags=["Outreach"])
async def get_lead_outreach(lead_id: str):
    """Generate A/B email + LinkedIn outreach for a lead."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")
    return await generate_outreach(lead)


# ── Buying Committee Graph ─────────────────────────────────────────────────────

@app.get("/api/graph", tags=["Graph"])
def all_graphs(min_committee_size: int = Query(1, ge=1)):
    """All company buying committee graphs (sorted by strength)."""
    leads = get_leads()
    scores = {l["id"]: compute_score(l)["score"] for l in leads}
    committees = get_all_committees(leads, scores)
    # Filter by size
    filtered = [c for c in committees if c.get("node_count", 0) >= min_committee_size]
    return {
        "total_companies": len(filtered),
        "committees": filtered[:100],  # cap for performance
    }


@app.get("/api/graph/{company}", tags=["Graph"])
def company_graph(company: str):
    """Buying committee graph for a specific company name."""
    leads = get_leads()
    scores = {l["id"]: compute_score(l)["score"] for l in leads}
    result = get_buying_committee(company, leads, scores)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── A/B Testing ───────────────────────────────────────────────────────────────

@app.get("/api/ab-testing", tags=["A/B Testing"])
def ab_testing_stats():
    """A/B performance analysis from CSV engagement data."""
    leads = get_leads()
    performance = analyse_ab_performance(leads)
    registry_summary = get_ab_summary()
    return {
        "historical_analysis": performance,
        "session_registry": registry_summary,
    }


@app.post("/api/ab-testing/register", tags=["A/B Testing"])
def register_variant(data: ABRegister):
    """Register that a variant was sent to a lead."""
    register_ab_send(data.lead_id, data.channel, data.variant)
    return {"registered": True, "lead_id": data.lead_id, "variant": data.variant}


@app.post("/api/ab-testing/response", tags=["A/B Testing"])
def record_ab_response(data: ResponseSignal):
    """Record a response event on a tracked A/B send."""
    result = ab_record(data.lead_id, data.response_type)
    return result


# ── Response Learning ─────────────────────────────────────────────────────────

@app.post("/api/learn/response", tags=["Learning"])
def submit_response(data: ResponseSignal):
    """
    Submit a prospect response to update scoring weights.
    Triggers re-scoring weight adjustment.
    """
    result = learn_record(data.lead_id, data.response_type)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    _invalidate_cache()  # force re-score on next request
    return result


@app.get("/api/learn/stats", tags=["Learning"])
def learning_stats():
    """Current state of the response learning agent."""
    return get_learning_stats()


@app.post("/api/learn/reset", tags=["Learning"])
def reset_learning_weights():
    """Reset all learning adjustments to baseline weights."""
    result = reset_learning()
    _invalidate_cache()
    return result


# ── Pipeline Status ───────────────────────────────────────────────────────────

@app.get("/api/pipeline", tags=["Pipeline"])
def pipeline_status():
    """System pipeline status: agents, data sources, and health."""
    leads = get_leads()
    scored = _get_scored()
    hot = sum(1 for l in scored if l["ml_score"]["tier"] == "Hot")
    warm = sum(1 for l in scored if l["ml_score"]["tier"] == "Warm")
    cold = sum(1 for l in scored if l["ml_score"]["tier"] == "Cold")
    return {
        "pipeline": "NeuroLead v1.0",
        "agents": {
            "SignalDiscoveryAgent": {
                "status": "active",
                "source": "csv_fallback (Apollo CSV)",
                "leads_processed": len(leads),
            },
            "EnrichmentAgent": {
                "status": "active",
                "source": "csv_fallback",
                "clay_api": bool(os.getenv("CLAY_API_KEY")),
                "apollo_api": bool(os.getenv("APOLLO_API_KEY")),
            },
            "MLScoringEngine": {
                "status": "active",
                "leads_scored": len(scored),
                "model": "Weighted Feature Scoring (ICP + Intent + Trigger + Seniority)",
                "effective_weights": get_effective_weights(),
            },
            "BuyingCommitteeGraphEngine": {
                "status": "active",
                "library": "networkx",
                "algorithm": "degree + betweenness centrality",
            },
            "LLMOutreachAgent": {
                "status": "active",
                "primary_llm": "clay_claygent",
                "clay_configured": bool(os.getenv("CLAY_API_KEY") and os.getenv("CLAY_TABLE_ID")),
                "fallback_llm": "gemini_flash",
                "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
                "final_fallback": "CSV templates (always available)",
                "variants_generated": "A/B per lead (email + linkedin)",
            },
            "ABTestingAgent": {
                "status": "active",
                "sessions_tracked": get_ab_summary()["total_tracked"],
            },
            "ResponseLearningAgent": {
                "status": "active",
                **get_learning_stats(),
            },
        },
        "lead_classification": {
            "hot": hot,
            "warm": warm,
            "cold": cold,
            "total": len(scored),
        },
        "data_sources": {
            "primary": "Apollo CSV Export (901 leads)",
            "enrichment_fallback": "CSV columns (technologies, funding, keywords)",
            "clay_api": "configured" if os.getenv("CLAY_API_KEY") else "not configured",
            "apollo_api": "configured" if os.getenv("APOLLO_API_KEY") else "not configured",
            "gemini_api": "configured" if os.getenv("GEMINI_API_KEY") else "not configured",
        },
    }


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 4000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
