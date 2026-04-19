"""
Enrichment Agent
----------------
Attempts to enrich a lead via Clay / Apollo APIs.
Falls back to the CSV data when API keys are not configured
or the API returns no additional info.
"""

import os
import re
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

CLAY_API_KEY = os.getenv("CLAY_API_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

APOLLO_PEOPLE_ENDPOINT = "https://api.apollo.io/v1/people/match"
CLAY_ENRICH_ENDPOINT = "https://api.clay.com/v1/enrich/person"  # placeholder


async def _try_apollo_enrich(email: str, name: str, company: str) -> Optional[dict]:
    """Attempt live Apollo enrichment. Returns None on failure."""
    if not APOLLO_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                APOLLO_PEOPLE_ENDPOINT,
                json={
                    "api_key": APOLLO_API_KEY,
                    "email": email,
                    "first_name": name.split()[0] if name else "",
                    "last_name": name.split()[-1] if name else "",
                    "organization_name": company,
                },
            )
            if resp.status_code == 200:
                data = resp.json().get("person", {})
                if data:
                    return {
                        "source": "apollo_api",
                        "headline": data.get("headline"),
                        "seniority": data.get("seniority"),
                        "linkedin_url": data.get("linkedin_url"),
                        "phone": data.get("phone_numbers", [{}])[0].get("sanitized_number")
                        if data.get("phone_numbers") else None,
                        "departments": ", ".join(data.get("departments", [])),
                        "twitter": data.get("twitter_url"),
                    }
    except Exception:
        pass
    return None


async def _try_clay_enrich(email: str) -> Optional[dict]:
    """Attempt live Clay enrichment. Returns None on failure."""
    if not CLAY_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                CLAY_ENRICH_ENDPOINT,
                headers={"Authorization": f"Bearer {CLAY_API_KEY}"},
                json={"email": email},
            )
            if resp.status_code == 200:
                return {"source": "clay_api", **resp.json()}
    except Exception:
        pass
    return None


def _csv_fallback(lead: dict) -> dict:
    """Build enrichment payload entirely from CSV fields."""
    return {
        "source": "csv_fallback",
        "name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
        "title": lead.get("title", ""),
        "company": lead.get("company", ""),
        "email": lead.get("email", ""),
        "email_status": lead.get("email_status", ""),
        "seniority": lead.get("seniority", ""),
        "departments": lead.get("departments", ""),
        "industry": lead.get("industry", ""),
        "employees": lead.get("employees"),
        "country": lead.get("country", ""),
        "city": lead.get("city", ""),
        "linkedin_url": lead.get("linkedin_url", ""),
        "website": lead.get("website", ""),
        "technologies": lead.get("technologies", ""),
        "annual_revenue": lead.get("annual_revenue"),
        "total_funding": lead.get("total_funding"),
        "latest_funding": lead.get("latest_funding", ""),
        "latest_funding_amount": lead.get("latest_funding_amount"),
        "last_raised_at": lead.get("last_raised_at", ""),
        "keywords_snippet": (lead.get("keywords", "") or "")[:300],
        "apollo_contact_id": lead.get("apollo_contact_id", ""),
        "apollo_account_id": lead.get("apollo_account_id", ""),
    }


async def enrich_lead(lead: dict) -> dict:
    """
    Main enrichment entry point.
    Tries Clay → Apollo → CSV fallback in order.
    Returns merged enrichment dict.
    """
    email = lead.get("email", "")
    name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
    company = lead.get("company", "")

    # Try live APIs first
    clay_data = await _try_clay_enrich(email)
    if clay_data:
        return {**_csv_fallback(lead), **clay_data, "source": "clay_api"}

    apollo_data = await _try_apollo_enrich(email, name, company)
    if apollo_data:
        return {**_csv_fallback(lead), **apollo_data, "source": "apollo_api"}

    # Always available: CSV data
    return _csv_fallback(lead)


def enrich_lead_sync(lead: dict) -> dict:
    """Synchronous fallback that always uses CSV data."""
    return _csv_fallback(lead)
