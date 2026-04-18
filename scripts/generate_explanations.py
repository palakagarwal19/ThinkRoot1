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
    "docs",
    "lead_explanations.md"
)

with open(INPUT_FILE,"r",encoding="utf-8") as file:

    reader = csv.DictReader(file)

    leads = list(reader)


with open(OUTPUT_FILE,"w",encoding="utf-8") as out:

    out.write("# Lead Scoring Explanations\n\n")

    for lead in leads:

        company = lead["company"]

        employees = lead["employees"]

        tech = lead["tech_stack"]

        out.write(
f"""
## {company}

Why Hot Lead?

- Large enterprise ({employees} employees)

- Strong technical fit:
{tech}

- Strong buyer persona:
{lead["title"]}

- Significant pain signal:
{lead["pain_signal"]}

- High funding/intent signal:
{lead["funding_stage"]}

----------------------------------------

"""
        )

print("Lead explanations generated.")