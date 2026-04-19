"""
LLM Outreach Reasoning Agent
-----------------------------
Generates personalised A/B outreach variants (email + LinkedIn) for each lead.

Priority chain:
  1. Clay API  – Claygent AI (if CLAY_API_KEY + CLAY_TABLE_ID are set)
  2. Gemini    – gemini-1.5-flash (if GEMINI_API_KEY is set)
  3. CSV data  – rule-based templates (always available)

Clay is used as the PRIMARY source because it is the enrichment backbone
of NeuroLead. When Clay receives a contact row it can run a Claygent prompt
to generate a personalised email and return the text via the row data.

Gemini acts as the intelligent LLM fallback when Clay is not configured.
CSV templates are the final guaranteed baseline.
"""

import os
import textwrap
import asyncio
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

CLAY_API_KEY   = os.getenv("CLAY_API_KEY", "")
CLAY_TABLE_ID  = os.getenv("CLAY_TABLE_ID", "")        # Clay table that has Claygent column
CLAY_BASE_URL  = "https://api.clay.com/v1"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Gemini client setup ───────────────────────────────────────────────────────
_gemini_model = None
try:
    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
except Exception:
    _gemini_model = None


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CLAY API  (Primary LLM for email generation)
# ═══════════════════════════════════════════════════════════════════════════════

async def _clay_generate(lead: dict, channel: str, variant: str) -> Optional[dict]:
    """
    Use Clay's table API + Claygent to generate personalised outreach.

    Flow:
      1. POST a new row to the configured Clay table with lead fields
      2. Poll the row until the Claygent column is populated (max 30 s)
      3. Extract the generated email/LinkedIn copy from the row columns

    Requires env vars:
      CLAY_API_KEY   – your Clay API key
      CLAY_TABLE_ID  – a Clay table configured with a Claygent column that
                       generates email copy from {{first_name}}, {{company}}, etc.
    """
    if not CLAY_API_KEY or not CLAY_TABLE_ID:
        return None

    headers = {
        "Authorization": f"Bearer {CLAY_API_KEY}",
        "Content-Type": "application/json",
    }

    # Build row payload with lead context
    name       = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
    company    = lead.get("company", "")
    title      = lead.get("title", "")
    industry   = lead.get("industry", "")
    funding    = lead.get("latest_funding", "")
    tech_snip  = (lead.get("technologies", "") or "")[:200]
    channel_lbl = "cold email" if channel == "email" else "LinkedIn DM"

    row_data = {
        "first_name":  lead.get("first_name", ""),
        "last_name":   lead.get("last_name", ""),
        "full_name":   name,
        "company":     company,
        "title":       title,
        "industry":    industry,
        "recent_funding": funding,
        "tech_stack":  tech_snip,
        "channel":     channel_lbl,
        "variant":     variant,
        "prompt_hint": (
            f"Write a personalised {channel_lbl} Variant {variant} for {name}, "
            f"{title} at {company}. Max 150 words. Include a subject line."
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Create row in Clay table
            create_resp = await client.post(
                f"{CLAY_BASE_URL}/tables/{CLAY_TABLE_ID}/rows",
                headers=headers,
                json={"rows": [row_data]},
            )
            if create_resp.status_code not in (200, 201):
                return None

            row_id = create_resp.json().get("rows", [{}])[0].get("id")
            if not row_id:
                return None

            # Poll for Claygent column result (up to 30 s)
            generated_text = None
            for _ in range(6):
                await asyncio.sleep(5)
                row_resp = await client.get(
                    f"{CLAY_BASE_URL}/tables/{CLAY_TABLE_ID}/rows/{row_id}",
                    headers=headers,
                )
                if row_resp.status_code == 200:
                    cols = row_resp.json().get("columns", {})
                    # Look for Claygent / generated_copy / email_copy column
                    for col_key in ("generated_copy", "claygent_output", "email_copy",
                                    "linkedin_copy", "ai_copy", "outreach"):
                        if cols.get(col_key):
                            generated_text = str(cols[col_key])
                            break
                    if generated_text:
                        break

            if not generated_text:
                return None

            # Parse Subject / Body from generated text
            subject, body = _parse_subject_body(generated_text)

            return {
                "variant":  variant,
                "channel":  channel,
                "subject":  subject or f"Re: {company} – quick thought",
                "body":     body or generated_text,
                "source":   "clay_claygent",
            }

    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GEMINI  (Fallback LLM)
# ═══════════════════════════════════════════════════════════════════════════════

async def _gemini_generate(lead: dict, channel: str, variant: str) -> Optional[dict]:
    """Call Gemini 1.5 Flash for outreach generation. Returns None on failure."""
    if not _gemini_model:
        return None
    try:
        name      = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
        company   = lead.get("company", "")
        title     = lead.get("title", "")
        industry  = lead.get("industry", "")
        funding   = lead.get("latest_funding", "none")
        tech_snip = (lead.get("technologies", "") or "")[:200]

        prompt = f"""You are an expert B2B sales copywriter for P95.ai (platform engineering consultancy).
Write a short, personalised {channel} outreach message Variant {variant} for:

Name: {name}
Title: {title}
Company: {company}
Industry: {industry}
Recent funding: {funding}
Tech stack: {tech_snip}

Rules:
- Max 120 words (LinkedIn) or 180 words (email)
- Reference a specific company/role detail
- Clear call-to-action
- No hollow buzzwords
- Output ONLY in this format:
Subject: <subject line>
Body: <message body>
"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: _gemini_model.generate_content(prompt)
        )
        raw = response.text or ""
        subject, body = _parse_subject_body(raw)

        return {
            "variant": variant,
            "channel": channel,
            "subject": subject or f"Quick note – {company}",
            "body":    body or raw,
            "source":  "gemini_flash",
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CSV TEMPLATES  (Final guaranteed fallback)
# ═══════════════════════════════════════════════════════════════════════════════

def _csv_email_a(lead: dict) -> dict:
    subject = (lead.get("email_template_subject_line")
               or lead.get("email_template_subject")
               or f"Scaling engineering at {lead.get('company', 'your company')}")
    body = lead.get("email_template_body", "").strip()
    if not body:
        name    = lead.get("first_name", "there")
        company = lead.get("company", "your company")
        body = textwrap.dedent(f"""\
            Hi {name},

            Teams scaling engineering at {company} often hit the same wall—
            CI/CD gets slower, deployments get riskier, and platform onboarding drags.

            We help engineering orgs standardise "golden paths" for CI/CD,
            improve observability, and accelerate platform onboarding—
            typically boosting deploy frequency 2–3×.

            Open to a 12-minute chat to see if this fits {company}?

            Best,
            [Your Name]
        """)
    return {"variant": "A", "channel": "email", "subject": subject, "body": body, "source": "csv_template"}


def _csv_email_b(lead: dict) -> dict:
    name    = lead.get("first_name", "there")
    company = lead.get("company", "your company")
    title   = lead.get("title", "")
    industry = lead.get("industry", "technology")
    funding = lead.get("latest_funding", "")
    funding_line = f" (congrats on the {funding}!)" if funding else ""
    subject = f"Quick question for the {title} at {company}"
    body = textwrap.dedent(f"""\
        Hi {name},

        I noticed {company}{funding_line} and wanted to reach out.

        Most {industry} engineering leaders tell us the hardest part of scaling
        isn't the product roadmap—it's keeping the platform reliable while
        shipping faster. We create repeatable deploy workflows, cut incident
        noise, and give teams observability to catch issues before users do.

        Would a 15-minute call make sense to see if we can help {company}?

        Best,
        [Your Name]
    """)
    return {"variant": "B", "channel": "email", "subject": subject, "body": body, "source": "csv_template_b"}


def _csv_linkedin_a(lead: dict) -> dict:
    subject = lead.get("linkedin_dm_subject") or "Quick thought for you"
    body    = lead.get("linkedin_dm") or lead.get("linkedin_dm_alt", "").strip()
    if not body:
        name    = lead.get("first_name", "there")
        company = lead.get("company", "your company")
        body = (f"Hi {name}—at {company}, are you looking to ship faster without "
                f"adding infra risk? We help teams set up golden-path pipelines "
                f"in a few weeks. Open to a 10-min chat?")
    return {"variant": "A", "channel": "linkedin", "subject": subject, "body": body, "source": "csv_template"}


def _csv_linkedin_b(lead: dict) -> dict:
    name    = lead.get("first_name", "there")
    company = lead.get("company", "your company")
    tech    = lead.get("technologies", "").lower()
    if "kubernetes" in tech or "docker" in tech:
        hook = f"noticed {company} runs Kubernetes—curious about your platform scaling approach"
    elif "aws" in tech or "azure" in tech:
        hook = f"saw {company}'s cloud footprint and wondered about deployment velocity"
    else:
        hook = f"saw {company}'s engineering growth"
    body = (f"Hi {name}—{hook}. We help CTOs reduce deployment friction by ~40% "
            f"with a simple golden-path setup. Worth a 10-min chat?")
    return {"variant": "B", "channel": "linkedin", "subject": f"Quick note for {name}", "body": body, "source": "csv_template_b"}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_subject_body(raw: str) -> tuple[str, str]:
    """Extract Subject / Body from LLM response text."""
    subject = ""
    body = raw.strip()
    if "Subject:" in raw and "Body:" in raw:
        parts = raw.split("Body:", 1)
        subject = parts[0].replace("Subject:", "").strip()
        body    = parts[1].strip()
    elif "Subject:" in raw:
        lines   = raw.split("\n", 1)
        subject = lines[0].replace("Subject:", "").strip()
        body    = lines[1].strip() if len(lines) > 1 else ""
    return subject, body


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_outreach(lead: dict) -> dict:
    """
    Generate full A/B outreach package for a lead.

    Priority for Variant B generation:
      Clay Claygent → Gemini → CSV rule-based template

    Variant A always comes from CSV (most field-tested copy).
    """
    # Variant A: always CSV (battle-tested copy from Apollo export)
    email_a    = _csv_email_a(lead)
    linkedin_a = _csv_linkedin_a(lead)

    # Variant B: try Clay → Gemini → CSV baseline
    email_b    = _csv_email_b(lead)
    linkedin_b = _csv_linkedin_b(lead)

    # Run Clay + Gemini concurrently for Variant B
    clay_email_b, clay_linkedin_b, gem_email_b, gem_linkedin_b = await asyncio.gather(
        _clay_generate(lead, "email",    "B"),
        _clay_generate(lead, "linkedin", "B"),
        _gemini_generate(lead, "email",    "B"),
        _gemini_generate(lead, "linkedin", "B"),
        return_exceptions=True,
    )

    # Apply best available result (Clay wins over Gemini)
    if isinstance(clay_email_b, dict):
        email_b = clay_email_b
    elif isinstance(gem_email_b, dict):
        email_b = gem_email_b

    if isinstance(clay_linkedin_b, dict):
        linkedin_b = clay_linkedin_b
    elif isinstance(gem_linkedin_b, dict):
        linkedin_b = gem_linkedin_b

    return {
        "lead_id":   lead.get("id"),
        "lead_name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
        "company":   lead.get("company", ""),
        "generation_priority": "Clay Claygent → Gemini → CSV templates",
        "email": {
            "variant_a":   email_a,
            "variant_b":   email_b,
            "recommended": "A",
        },
        "linkedin": {
            "variant_a":   linkedin_a,
            "variant_b":   linkedin_b,
            "recommended": "A",
        },
        "generation_sources": {
            "email_a":    email_a["source"],
            "email_b":    email_b["source"],
            "linkedin_a": linkedin_a["source"],
            "linkedin_b": linkedin_b["source"],
        },
    }
