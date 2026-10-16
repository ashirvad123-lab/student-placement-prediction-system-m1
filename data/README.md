# Dataset

`placement_data.csv` is generated locally by `generate_synthetic_data.py`.
Every generated record is synthetic and is not based on real student records.
It is intended for demonstrating the software workflow, not estimating actual
placement outcomes.

Run the generator from the project root:

```powershell
py data\generate_synthetic_data.py
```

The CSV has one row per synthetic student and the following columns:

| Column | Meaning |
| --- | --- |
| `CGPA` | CGPA from 0 to 10 |
| `Tenth_Percentage` | 10th grade percentage, 0 to 100 |
| `Twelfth_Percentage` | 12th grade percentage, 0 to 100 |
| `Branch` | Student's academic branch |
| `Backlogs` | Number of backlogs |
| `Internship_Experience` | `Yes` or `No` |
| `Technical_Skill_Level` | `Beginner`, `Intermediate`, or `Advanced` |
| `Aptitude_Score` | Score from 0 to 100 |
| `Communication_Skills` | Score from 0 to 10 |
| `Projects_Completed` | Number of completed projects |
| `Placement_Status` | Target label: `Placed` or `Not Placed` |

The target is generated from a transparent synthetic scoring rule plus random
variation. As a result, model metrics from this data only demonstrate the
training and evaluation process; they are not evidence of real-world accuracy.
