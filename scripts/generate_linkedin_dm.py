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
    "linkedin_dm_variants.md"
)

with open(
    INPUT_FILE,
    mode="r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    leads = list(reader)


with open(
    OUTPUT_FILE,
    mode="w",
    encoding="utf-8"
) as out:

    out.write("# LinkedIn DM Variants\n\n")

    for lead in leads:

        company = lead["company"]

        name = lead["contact_name"]

        pain = lead["pain_signal"]


        out.write(
f"""
## {company}

### LinkedIn DM Variant A

Hi {name},

Saw your team may be dealing with:

{pain}

We’ve seen similar engineering teams use P95 to improve reliability and reduce AI observability gaps.

Would love to compare notes.


---

### LinkedIn DM Variant B

Hi {name},

Noticed {company} is scaling aggressively.

Curious whether AI reliability or observability has become a focus for your team.

Open to connect?

=================================================

"""
        )

print("LinkedIn DM variants generated.")