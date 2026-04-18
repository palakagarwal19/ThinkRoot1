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
    "scored_leads.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "top20_hot_leads.csv"
)


rows = []

with open(
    INPUT_FILE,
    mode="r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        rows.append(row)


rows.sort(
    key=lambda x: int(x["lead_score"]),
    reverse=True
)


top20 = rows[:20]


with open(
    OUTPUT_FILE,
    mode="w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=top20[0].keys()
    )

    writer.writeheader()

    writer.writerows(top20)


print("Top 20 leads selected.")
print("Output saved in top20_hot_leads.csv")