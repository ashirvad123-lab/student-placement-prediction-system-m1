"""Focused tests for the training and inference pipeline."""

import csv
from pathlib import Path

from placement.ml.predict import predict_placement
from placement.ml.train_model import train_and_evaluate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_train_compare_and_predict(tmp_path):
    """Train all candidates, save outputs, and predict using the saved pipeline."""
    dataset = PROJECT_ROOT / "data" / "placement_data.csv"
    if not dataset.is_file():
        raise AssertionError(
            "Generate the synthetic dataset first with "
            "'py data\\generate_synthetic_data.py'."
        )

    model_path = tmp_path / "placement_model.joblib"
    metrics_path = tmp_path / "model_metrics.json"
    report = train_and_evaluate(
        dataset_path=dataset,
        model_path=model_path,
        metrics_path=metrics_path,
    )

    assert model_path.is_file()
    assert metrics_path.is_file()
    assert set(report["models"]) == {
        "Logistic Regression",
        "Decision Tree",
        "Random Forest",
        "Support Vector Machine",
    }
    assert report["synthetic_data"] is True
    assert len(report["confusion_matrix"]) == 2

    with dataset.open(newline="", encoding="utf-8") as dataset_file:
        sample = next(csv.DictReader(dataset_file))

    features = {
        "CGPA": float(sample["CGPA"]),
        "Tenth_Percentage": float(sample["Tenth_Percentage"]),
        "Twelfth_Percentage": float(sample["Twelfth_Percentage"]),
        "Branch": sample["Branch"],
        "Backlogs": int(sample["Backlogs"]),
        "Internship_Experience": sample["Internship_Experience"],
        "Technical_Skill_Level": sample["Technical_Skill_Level"],
        "Aptitude_Score": float(sample["Aptitude_Score"]),
        "Communication_Skills": float(sample["Communication_Skills"]),
        "Projects_Completed": int(sample["Projects_Completed"]),
    }
    prediction = predict_placement(features, model_path=model_path)
    assert prediction["predicted_status"] in {"Placed", "Not Placed"}
    assert prediction["model_name"] == report["selected_model"]
    assert 0.0 <= prediction["placement_probability"] <= 1.0
