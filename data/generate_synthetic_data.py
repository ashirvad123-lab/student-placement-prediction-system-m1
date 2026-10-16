"""Create a reproducible, explicitly synthetic placement demonstration dataset."""

import csv
import random
from pathlib import Path


OUTPUT_PATH = Path(__file__).resolve().parent / "placement_data.csv"
RECORD_COUNT = 500
BRANCHES = ["CSE", "IT", "ECE", "EEE", "Mechanical", "Civil"]
SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"]


def create_record(rng):
    """Generate one synthetic student and a noisy illustrative target label."""
    cgpa = round(rng.uniform(5.0, 10.0), 2)
    tenth = round(rng.uniform(50.0, 100.0), 2)
    twelfth = round(rng.uniform(50.0, 100.0), 2)
    branch = rng.choice(BRANCHES)
    backlogs = rng.choices([0, 1, 2, 3], weights=[72, 17, 8, 3])[0]
    internship = rng.choices(["Yes", "No"], weights=[42, 58])[0]
    skills = rng.choices(SKILL_LEVELS, weights=[25, 48, 27])[0]
    aptitude = round(rng.uniform(20.0, 100.0), 2)
    communication = round(rng.uniform(2.0, 10.0), 2)
    projects = rng.choices([0, 1, 2, 3, 4, 5], weights=[8, 20, 27, 23, 15, 7])[0]

    # The score is for creating demo labels only, not a real hiring formula.
    score = (
        (cgpa - 5.0) * 0.75
        + ((tenth + twelfth) / 2 - 50.0) * 0.025
        + aptitude * 0.018
        + communication * 0.12
        + projects * 0.18
        + (0.45 if internship == "Yes" else 0)
        + {"Beginner": 0, "Intermediate": 0.2, "Advanced": 0.4}[skills]
        - backlogs * 0.35
        + (0.12 if branch in {"CSE", "IT", "ECE"} else 0)
        + rng.uniform(-0.9, 0.9)
    )
    status = "Placed" if score >= 4.2 else "Not Placed"

    return {
        "CGPA": cgpa,
        "Tenth_Percentage": tenth,
        "Twelfth_Percentage": twelfth,
        "Branch": branch,
        "Backlogs": backlogs,
        "Internship_Experience": internship,
        "Technical_Skill_Level": skills,
        "Aptitude_Score": aptitude,
        "Communication_Skills": communication,
        "Projects_Completed": projects,
        "Placement_Status": status,
    }


def main():
    rng = random.Random(20261015)
    columns = [
        "CGPA",
        "Tenth_Percentage",
        "Twelfth_Percentage",
        "Branch",
        "Backlogs",
        "Internship_Experience",
        "Technical_Skill_Level",
        "Aptitude_Score",
        "Communication_Skills",
        "Projects_Completed",
        "Placement_Status",
    ]

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as dataset_file:
        writer = csv.DictWriter(dataset_file, fieldnames=columns)
        writer.writeheader()
        for _ in range(RECORD_COUNT):
            writer.writerow(create_record(rng))

    print(f"Created {RECORD_COUNT} synthetic records at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
