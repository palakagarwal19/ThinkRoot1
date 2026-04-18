import csv
import os
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "scored_leads.csv"
)

scores = []

hot = 0
warm = 0
cold = 0

companies = []
top_scores = []


with open(INPUT_FILE,"r",encoding="utf-8") as file:

    reader = csv.DictReader(file)

    rows = list(reader)

    for row in rows:

        score = int(
            row["lead_score"]
        )

        scores.append(score)

        if row["tier"]=="Hot":
            hot += 1

        elif row["tier"]=="Warm":
            warm += 1

        else:
            cold += 1


rows.sort(
    key=lambda x:int(x["lead_score"]),
    reverse=True
)

top10 = rows[:10]

for lead in top10:

    companies.append(
        lead["company"]
    )

    top_scores.append(
        int(lead["lead_score"])
    )


# Chart 1

plt.figure()

plt.bar(
    ["Hot","Warm","Cold"],
    [hot,warm,cold]
)

plt.title(
    "Lead Classification"
)

plt.show()


# Chart 2

plt.figure()

plt.hist(scores)

plt.title(
    "Lead Score Distribution"
)

plt.show()


# Chart 3

plt.figure()

plt.bar(
    companies,
    top_scores
)

plt.title(
    "Top 10 Leads"
)

plt.xticks(rotation=45)

plt.show()