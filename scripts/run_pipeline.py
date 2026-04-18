import os

scripts = [
    "score_leads.py",
    "select_top20.py",
    "generate_outreach.py",
    "generate_linkedin_dm.py",
    "generate_hypotheses.py",
    "generate_explanations.py"
]

for script in scripts:

    print(f"Running {script}...")

    os.system(
        f'python "{os.path.join(os.path.dirname(__file__), script)}"'
    )

print("\nPipeline complete.")