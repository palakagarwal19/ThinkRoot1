"""
NeuroLead CSV Data Loader
-------------------------
Loads and normalizes the Apollo contacts CSV export into internal Lead schema.
Falls back gracefully for any missing columns.
"""

import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.getenv(
    "LEADS_CSV_PATH",
    str(Path(__file__).parent.parent / "apollo-contacts-export-(2)-(1)-Default-view-export-1776574386695.csv"),
)

# ── column aliases (CSV header → internal key) ──────────────────────────────
COL_MAP = {
    "First Name": "first_name",
    "Last Name": "last_name",
    "Title": "title",
    "Company Name": "company",
    "Email": "email",
    "Email Status": "email_status",
    "Seniority": "seniority",
    "Departments": "departments",
    "# Employees": "employees",
    "Industry": "industry",
    "Keywords": "keywords",
    "Person Linkedin Url": "linkedin_url",
    "Website": "website",
    "Company Linkedin Url": "company_linkedin_url",
    "City": "city",
    "State": "state",
    "Country": "country",
    "Company City": "company_city",
    "Company Country": "company_country",
    "Technologies": "technologies",
    "Annual Revenue": "annual_revenue",
    "Total Funding": "total_funding",
    "Latest Funding": "latest_funding",
    "Latest Funding Amount": "latest_funding_amount",
    "Last Raised At": "last_raised_at",
    "ICP Industry Match": "icp_match",
    "Recent Funding": "recent_funding",
    "Likely Modern Stack": "modern_stack",
    "Lead Tier": "lead_tier_csv",
    "Lead Score": "lead_score_csv",
    "Cold Email Template": "email_template_subject",
    "Cold Email Template subject": "email_template_subject_line",
    "Email Template body": "email_template_body",
    "LinkedIn DM Copy": "linkedin_dm",
    "Linked In DM Copy subject": "linkedin_dm_subject",
    "Linkedln DM": "linkedin_dm_alt",
    "Lead Tier Classification": "lead_tier_classification",
    "Apollo Contact Id": "apollo_contact_id",
    "Apollo Account Id": "apollo_account_id",
    "Email Sent": "email_sent",
    "Email Open": "email_open",
    "Email Bounced": "email_bounced",
    "Replied": "replied",
    "Demoed": "demoed",
}


def _safe_str(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return str(val).strip()


def _safe_float(val) -> Optional[float]:
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return None


def _bool_flag(val) -> bool:
    s = _safe_str(val).lower()
    return s in ("true", "yes", "1", "y")


def _generate_id(idx: int, apollo_id: str) -> str:
    if apollo_id:
        return apollo_id
    return f"lead_{idx:04d}"


def load_leads() -> list[dict]:
    """Load and normalise all leads from the CSV. Returns list of dicts."""
    path = Path(CSV_PATH)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found at {path.resolve()}")

    df = pd.read_csv(path, dtype=str, on_bad_lines="skip")

    # Rename only the columns that exist
    rename = {k: v for k, v in COL_MAP.items() if k in df.columns}
    df.rename(columns=rename, inplace=True)

    # Ensure required columns exist even if missing
    for col in COL_MAP.values():
        if col not in df.columns:
            df[col] = ""

    leads = []
    for idx, row in df.iterrows():
        apollo_id = _safe_str(row.get("apollo_contact_id", ""))
        lead_id = _generate_id(idx, apollo_id)

        lead = {
            "id": lead_id,
            "first_name": _safe_str(row.get("first_name")),
            "last_name": _safe_str(row.get("last_name")),
            "title": _safe_str(row.get("title")),
            "company": _safe_str(row.get("company")),
            "email": _safe_str(row.get("email")),
            "email_status": _safe_str(row.get("email_status")),
            "seniority": _safe_str(row.get("seniority")),
            "departments": _safe_str(row.get("departments")),
            "employees": _safe_int(row.get("employees")),
            "industry": _safe_str(row.get("industry")),
            "keywords": _safe_str(row.get("keywords")),
            "linkedin_url": _safe_str(row.get("linkedin_url")),
            "website": _safe_str(row.get("website")),
            "company_linkedin_url": _safe_str(row.get("company_linkedin_url")),
            "city": _safe_str(row.get("city")),
            "state": _safe_str(row.get("state")),
            "country": _safe_str(row.get("country")),
            "company_city": _safe_str(row.get("company_city")),
            "company_country": _safe_str(row.get("company_country")),
            "technologies": _safe_str(row.get("technologies")),
            "annual_revenue": _safe_float(row.get("annual_revenue")),
            "total_funding": _safe_float(row.get("total_funding")),
            "latest_funding": _safe_str(row.get("latest_funding")),
            "latest_funding_amount": _safe_float(row.get("latest_funding_amount")),
            "last_raised_at": _safe_str(row.get("last_raised_at")),
            "icp_match": _safe_str(row.get("icp_match")),
            "recent_funding": _safe_str(row.get("recent_funding")),
            "modern_stack": _safe_str(row.get("modern_stack")),
            "lead_tier_csv": _safe_str(row.get("lead_tier_csv")),
            "lead_score_csv": _safe_int(row.get("lead_score_csv")),
            "email_template_subject": _safe_str(row.get("email_template_subject")),
            "email_template_subject_line": _safe_str(row.get("email_template_subject_line")),
            "email_template_body": _safe_str(row.get("email_template_body")),
            "linkedin_dm": _safe_str(row.get("linkedin_dm")),
            "linkedin_dm_subject": _safe_str(row.get("linkedin_dm_subject")),
            "linkedin_dm_alt": _safe_str(row.get("linkedin_dm_alt")),
            "lead_tier_classification": _safe_str(row.get("lead_tier_classification")),
            "apollo_contact_id": apollo_id,
            "apollo_account_id": _safe_str(row.get("apollo_account_id")),
            "email_sent": _bool_flag(row.get("email_sent")),
            "email_open": _bool_flag(row.get("email_open")),
            "email_bounced": _bool_flag(row.get("email_bounced")),
            "replied": _bool_flag(row.get("replied")),
            "demoed": _bool_flag(row.get("demoed")),
        }
        leads.append(lead)

    return leads


# Singleton cache
_leads_cache: Optional[list[dict]] = None


def get_leads() -> list[dict]:
    """Return cached leads (loads once on first call)."""
    global _leads_cache
    if _leads_cache is None:
        _leads_cache = load_leads()
    return _leads_cache


def get_lead_by_id(lead_id: str) -> Optional[dict]:
    leads = get_leads()
    for lead in leads:
        if lead["id"] == lead_id:
            return lead
    return None


def reload_leads() -> list[dict]:
    """Force reload from disk."""
    global _leads_cache
    _leads_cache = None
    return get_leads()
