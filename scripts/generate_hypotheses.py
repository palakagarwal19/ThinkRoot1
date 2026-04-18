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
    "response_rate_hypotheses.md"
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

    out.write("# Response Rate Hypotheses\n\n")

    for lead in leads:

        company = lead["company"]

        title = lead["title"]

        pain = lead["pain_signal"]


        if "compliance" in pain.lower():
            hypothesis = (
                "Variant A likely performs better because risk/compliance messaging should resonate."
            )

        elif "scaling" in pain.lower():
            hypothesis = (
                "Variant B likely performs better because growth/scaling messaging should resonate."
            )

        else:
            hypothesis = (
                "Both variants may perform similarly; requires live testing."
            )


        out.write(
f"""
## {company} ({title})

Pain Signal:
{pain}

Hypothesis:
{hypothesis}

Expected Response Rate:

Variant A:
8-12%

Variant B:
5-10%

-----------------------------------------

"""
        )

print("Hypotheses generated.")