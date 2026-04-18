import csv
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "top20_hot_leads.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "outreach",
    "ab_variants.md"
)


def get_personalization(stack):

    stack = stack.lower()

    if "kubernetes" in stack:
        return "Kubernetes observability challenges"

    if "datadog" in stack:
        return "monitoring blind spots"

    if "terraform" in stack:
        return "infrastructure scaling complexity"

    if "openai" in stack:
        return "LLM reliability risks"

    return "production AI reliability issues"


with open(INPUT_FILE,"r",encoding="utf-8") as file:

    reader = csv.DictReader(file)

    leads = list(reader)


with open(OUTPUT_FILE,"w",encoding="utf-8") as out:

    out.write("# Personalized A/B Outreach\n\n")

    for lead in leads:

        company = lead["company"]

        tech_stack = lead["tech_stack"]

        personalization = get_personalization(
            tech_stack
        )

        out.write(
f"""
## {company}

Variant A

Subject:
Reducing {personalization} at {company}

Message:
Saw your team uses:

{tech_stack}

Many teams hit {personalization} as they scale.

P95 helps reduce that risk.

---

Variant B

Subject:
Scaling AI faster at {company}

Message:

Companies using {tech_stack}
often need stronger observability to scale reliably.

P95 may help.

================================================

"""
        )

print("Personalized outreach generated.")