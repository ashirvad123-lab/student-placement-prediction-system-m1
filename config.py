"""Application settings loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    MYSQL_CONFIG = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "placement_db"),
    }
    MODEL_PATH = BASE_DIR / os.getenv("MODEL_PATH", "models/placement_model.joblib")
    METRICS_PATH = BASE_DIR / os.getenv("METRICS_PATH", "models/model_metrics.json")
    DATASET_PATH = BASE_DIR / "data" / "placement_data.csv"


def validate_config():
    """Fail early when the app's secret key has not been configured."""
    if not Config.SECRET_KEY or Config.SECRET_KEY == "replace-this-with-a-long-random-secret":
        raise RuntimeError(
            "Set FLASK_SECRET_KEY in your .env file before starting the application."
        )
