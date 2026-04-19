"""
Buying Committee Graph Engine
------------------------------
Groups leads by company and builds a directed NetworkX graph
representing the buying committee for each account.

Nodes = individual leads (decision-makers)
Edges = inferred influence relationships based on seniority / department

Graph analytics:
  - Degree centrality
  - Betweenness centrality
  - Influence rank (composite)
  - Committee strength score
"""

from collections import defaultdict
from typing import Optional
import networkx as nx


# Seniority → numeric rank for influence edge direction
SENIORITY_RANK = {
    "founder": 10, "owner": 10,
    "c suite": 9, "c-suite": 9,
    "vp": 8, "partner": 7,
    "director": 6, "manager": 5,
    "senior": 4, "individual contributor": 3, "entry": 2,
}

DEPT_GROUPS = {
    "engineering": ["engineering", "technical", "devops", "infrastructure", "platform"],
    "product": ["product", "design", "ux"],
    "sales": ["sales", "business development", "revenue"],
    "finance": ["finance", "cfo", "accounting"],
    "it": ["information technology", "it", "operations"],
    "c_suite": ["c suite", "c-suite", "executive"],
}


def _seniority_rank(lead: dict) -> int:
    s = lead.get("seniority", "").lower()
    t = lead.get("title", "").lower()
    for level, rank in SENIORITY_RANK.items():
        if level in s or level in t:
            return rank
    return 1


def _dept_group(lead: dict) -> str:
    depts = lead.get("departments", "").lower()
    for group, keywords in DEPT_GROUPS.items():
        if any(kw in depts for kw in keywords):
            return group
    return "other"


def _node_attrs(lead: dict, score: int = 0) -> dict:
    return {
        "id": lead["id"],
        "name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
        "title": lead.get("title", ""),
        "seniority": lead.get("seniority", ""),
        "seniority_rank": _seniority_rank(lead),
        "department_group": _dept_group(lead),
        "email": lead.get("email", ""),
        "linkedin_url": lead.get("linkedin_url", ""),
        "lead_score": score,
    }


def build_company_graph(leads_for_company: list[dict], scores: Optional[dict] = None) -> nx.DiGraph:
    """
    Build a directed influence graph for a single company's buying committee.
    
    scores: dict of lead_id → int score (optional)
    """
    G = nx.DiGraph()
    scores = scores or {}

    for lead in leads_for_company:
        lid = lead["id"]
        score = scores.get(lid, 0)
        G.add_node(lid, **_node_attrs(lead, score))

    # Add directed edges: lower seniority → higher seniority (influence upward)
    nodes = list(leads_for_company)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            rank_a = _seniority_rank(a)
            rank_b = _seniority_rank(b)
            weight = abs(rank_a - rank_b) + 1
            if rank_a < rank_b:
                G.add_edge(a["id"], b["id"], weight=weight, relation="reports_to")
            elif rank_b < rank_a:
                G.add_edge(b["id"], a["id"], weight=weight, relation="reports_to")
            else:
                # Same level – peer relationship (bidirectional)
                G.add_edge(a["id"], b["id"], weight=1, relation="peer")
                G.add_edge(b["id"], a["id"], weight=1, relation="peer")

    return G


def compute_graph_analytics(G: nx.DiGraph) -> dict:
    """Compute centrality and influence metrics for a graph."""
    if G.number_of_nodes() == 0:
        return {"nodes": [], "edges": [], "committee_strength": 0}

    # Centrality metrics
    try:
        degree_cent = nx.degree_centrality(G)
        betweenness_cent = nx.betweenness_centrality(G, normalized=True)
        in_degree = dict(G.in_degree())
        out_degree = dict(G.out_degree())
    except Exception:
        degree_cent = betweenness_cent = {}
        in_degree = out_degree = {}

    # Composite influence score per node
    node_list = []
    for node_id, attrs in G.nodes(data=True):
        sr = attrs.get("seniority_rank", 1)
        dc = degree_cent.get(node_id, 0)
        bc = betweenness_cent.get(node_id, 0)
        # Influence = weighted combo
        influence = round((sr / 10) * 0.40 + dc * 0.35 + bc * 0.25, 4)
        node_list.append({
            **attrs,
            "degree_centrality": round(dc, 4),
            "betweenness_centrality": round(bc, 4),
            "in_degree": in_degree.get(node_id, 0),
            "out_degree": out_degree.get(node_id, 0),
            "influence_score": influence,
        })

    # Sort by influence descending
    node_list.sort(key=lambda x: x["influence_score"], reverse=True)

    # Edge list
    edge_list = [
        {
            "source": u,
            "target": v,
            "weight": d.get("weight", 1),
            "relation": d.get("relation", "unknown"),
        }
        for u, v, d in G.edges(data=True)
    ]

    # Committee strength = avg influence of top-3 nodes * size_factor
    top_influences = [n["influence_score"] for n in node_list[:3]]
    avg_top = sum(top_influences) / len(top_influences) if top_influences else 0
    size_factor = min(G.number_of_nodes() / 5.0, 1.0)
    committee_strength = round(avg_top * 100 * (0.7 + 0.3 * size_factor), 1)

    return {
        "nodes": node_list,
        "edges": edge_list,
        "committee_strength": committee_strength,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "top_influencer": node_list[0]["name"] if node_list else None,
    }


def get_buying_committee(company_name: str, all_leads: list[dict], scores: Optional[dict] = None) -> dict:
    """
    High-level API: build and analyse buying committee graph for a company.
    """
    company_leads = [
        l for l in all_leads
        if l.get("company", "").strip().lower() == company_name.strip().lower()
    ]

    if not company_leads:
        # Fuzzy match: partial company name
        company_leads = [
            l for l in all_leads
            if company_name.lower() in l.get("company", "").lower()
        ]

    if not company_leads:
        return {
            "company": company_name,
            "error": "No leads found for this company",
            "nodes": [], "edges": [], "committee_strength": 0,
        }

    G = build_company_graph(company_leads, scores)
    analytics = compute_graph_analytics(G)
    return {
        "company": company_name,
        "leads_found": len(company_leads),
        **analytics,
    }


def get_all_committees(all_leads: list[dict], scores: Optional[dict] = None) -> list[dict]:
    """Build committee graphs for every company with >1 lead."""
    companies = defaultdict(list)
    for lead in all_leads:
        co = lead.get("company", "").strip()
        if co:
            companies[co].append(lead)

    results = []
    for company, leads in companies.items():
        if len(leads) >= 1:
            result = get_buying_committee(company, all_leads, scores)
            results.append(result)

    results.sort(key=lambda x: x.get("committee_strength", 0), reverse=True)
    return results
