"""Train and compare four classifiers using one consistent preprocessing pipeline."""

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from config import Config

NUMERIC_FEATURES = [
    "CGPA",
    "Tenth_Percentage",
    "Twelfth_Percentage",
    "Backlogs",
    "Aptitude_Score",
    "Communication_Skills",
    "Projects_Completed",
]
CATEGORICAL_FEATURES = [
    "Branch",
    "Internship_Experience",
    "Technical_Skill_Level",
]
TARGET = "Placement_Status"
RANDOM_STATE = 42


def make_pipeline(classifier):
    """Build preprocessing and classifier together so inference matches training."""
    preprocess = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    return Pipeline([("preprocess", preprocess), ("classifier", classifier)])


def train_and_evaluate(dataset_path=None, model_path=None, metrics_path=None):
    """Fit candidate models, select by test F1, and save model and evaluation data."""
    dataset_path = Path(dataset_path or Config.DATASET_PATH)
    model_path = Path(model_path or Config.MODEL_PATH)
    metrics_path = Path(metrics_path or Config.METRICS_PATH)
    chart_path = metrics_path.with_name("confusion_matrix.png")

    data = pd.read_csv(dataset_path)
    expected_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]
    missing = sorted(set(expected_columns) - set(data.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")
    if data[expected_columns].isnull().any().any():
        raise ValueError("Dataset contains blank values in required feature columns.")
    if data[TARGET].nunique() != 2:
        raise ValueError("Placement_Status must contain exactly two classes.")

    features = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    target = data[TARGET].astype(str)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=target,
    )

    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=6, random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=8, random_state=RANDOM_STATE
        ),
        "Support Vector Machine": CalibratedClassifierCV(
            SVC(kernel="rbf", random_state=RANDOM_STATE),
            method="sigmoid",
            cv=3,
        ),
    }

    results = {}
    fitted_models = {}
    for name, classifier in candidates.items():
        pipeline = make_pipeline(classifier)
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        results[name] = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(
                precision_score(y_test, predictions, pos_label="Placed", zero_division=0)
            ),
            "recall": float(
                recall_score(y_test, predictions, pos_label="Placed", zero_division=0)
            ),
            "f1_score": float(
                f1_score(y_test, predictions, pos_label="Placed", zero_division=0)
            ),
        }
        fitted_models[name] = pipeline

    selected_name = max(
        results,
        key=lambda name: (
            results[name]["f1_score"],
            results[name]["accuracy"],
            name == "Logistic Regression",
        ),
    )
    selected_model = fitted_models[selected_name]
    final_predictions = selected_model.predict(x_test)
    labels = sorted(target.unique())
    matrix = confusion_matrix(y_test, final_predictions, labels=labels)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": selected_model,
            "model_name": selected_name,
            "feature_columns": NUMERIC_FEATURES + CATEGORICAL_FEATURES,
            "target_labels": labels,
        },
        model_path,
    )

    report = {
        "synthetic_data": True,
        "dataset_rows": int(len(data)),
        "test_rows": int(len(y_test)),
        "selection_metric": "F1-score for the Placed class; accuracy breaks ties",
        "selected_model": selected_name,
        "models": results,
        "confusion_matrix_labels": labels,
        "confusion_matrix": matrix.tolist(),
    }
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    plt.figure(figsize=(6, 5))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
    )
    plt.xlabel("Predicted status")
    plt.ylabel("Actual status")
    plt.title(f"{selected_name} - held-out test confusion matrix")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150)
    plt.close()

    return report


if __name__ == "__main__":
    result = train_and_evaluate()
    print(json.dumps(result, indent=2))
