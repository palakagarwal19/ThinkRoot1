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
    "enriched_leads.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "scored_leads.csv"
)


def score_company_fit(employees):
    score = 0

    if employees >= 500:
        score += 5
    if employees >= 1000:
        score += 5
    if employees >= 5000:
        score += 5
    if employees >= 7000:
        score += 5
    if employees >= 10000:
        score += 5

    return min(score,25)


def score_tech_stack(stack):

    score = 0

    keywords = [
        "AWS",
        "Azure",
        "GCP",
        "Kubernetes",
        "Terraform",
        "Docker",
        "OpenAI"
    ]

    for tech in keywords:
        if tech.lower() in stack.lower():
            score += 5

    return min(score,20)


def score_pain(signal):

    signal = signal.lower()

    if "compliance" in signal:
        return 20

    if "reliability" in signal:
        return 18

    if "scaling" in signal:
        return 15

    return 10


def score_buyer(title):

    title = title.lower()

    if "cto" in title:
        return 20

    if "vp engineering" in title:
        return 18

    if "head" in title:
        return 15

    if "director" in title:
        return 12

    return 5


def score_intent(funding):

    funding = funding.lower()

    if "public" in funding:
        return 15

    if "series e" in funding:
        return 12

    if "series d" in funding:
        return 10

    return 8


def classify(score):

    if score >= 80:
        return "Hot"

    elif score >= 60:
        return "Warm"

    else:
        return "Cold"


rows_scored = []

with open(
    INPUT_FILE,
    mode="r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        # skip empty/broken rows
        if not row["employees"]:
            continue

        employees = int(
            row["employees"]
        )

        total_score = (
            score_company_fit(employees)
            + score_tech_stack(row["tech_stack"])
            + score_pain(row["pain_signal"])
            + score_buyer(row["title"])
            + score_intent(row["funding_stage"])
        )

        row["lead_score"] = total_score

        row["tier"] = classify(
            total_score
        )

        rows_scored.append(row)


with open(
    OUTPUT_FILE,
    mode="w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=rows_scored[0].keys()
    )

    writer.writeheader()

    writer.writerows(rows_scored)


print("Lead scoring complete.")
print("Output saved in scored_leads.csv")