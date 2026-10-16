"""Load the saved preprocessing/model pipeline and predict one student's status."""

from pathlib import Path

import joblib
import pandas as pd

from config import Config
from placement.ml.train_model import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def predict_placement(student_features, model_path=None):
    """Return predicted label, probability for Placed, and selected model name."""
    model_path = Path(model_path or Config.MODEL_PATH)
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Trained model not found at {model_path}. Train the model first."
        )

    required = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    missing = [feature for feature in required if feature not in student_features]
    if missing:
        raise ValueError(f"Missing prediction fields: {', '.join(missing)}")

    model_bundle = joblib.load(model_path)
    row = pd.DataFrame([{feature: student_features[feature] for feature in required}])
    pipeline = model_bundle["pipeline"]
    predicted_status = str(pipeline.predict(row)[0])

    probability = None
    if hasattr(pipeline, "predict_proba"):
        class_labels = list(pipeline.classes_)
        if "Placed" in class_labels:
            placed_index = class_labels.index("Placed")
            probability = float(pipeline.predict_proba(row)[0][placed_index])

    return {
        "predicted_status": predicted_status,
        "placement_probability": probability,
        "model_name": model_bundle["model_name"],
    }
