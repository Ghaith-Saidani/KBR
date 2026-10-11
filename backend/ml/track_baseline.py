from __future__ import annotations

import hashlib
import json
from pathlib import Path

import mlflow
import pandas as pd

DATASET_PATH = Path("data/processed/user_activities.csv")
REPORT_PATH = Path("data/reports/baseline_evaluation_report.json")
SCRIPT_PATH = Path("backend/ml/evaluate_baseline.py")

TRACKING_DB = Path("mlflow.db")
EXPERIMENT_NAME = "KBR-Anomaly-Detection"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log_metric_if_valid(name: str, value) -> None:
    if value is None:
        return

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return

    if pd.notna(numeric):
        mlflow.log_metric(name, numeric)


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Baseline report not found: {REPORT_PATH}. "
            "Run python -m backend.ml.evaluate_baseline first."
        )

    with REPORT_PATH.open(encoding="utf-8") as file:
        report = json.load(file)

    dataset_hash = sha256_file(DATASET_PATH)
    dataset_size = DATASET_PATH.stat().st_size
    dataset_rows = len(pd.read_csv(DATASET_PATH))

    TRACKING_DB.parent.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{TRACKING_DB.resolve().as_posix()}")
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="isolation-forest-baseline-evaluation"):
        mlflow.set_tags({
            "project": "KBR",
            "task": "unsupervised-anomaly-detection",
            "evaluation_type": "chronological-drift-diagnostics",
            "models_saved": "false",
            "labels_available": "false",
        })

        mlflow.log_params({
            "model_type": report["model_type"],
            "report_version": report["report_version"],
            "dataset_sha256": dataset_hash,
            "dataset_rows": dataset_rows,
            "dataset_size_bytes": dataset_size,
            "http_rows": report["http_rows"],
            "business_rows": report["business_rows"],
            "existing_models_modified": report["existing_models_modified"],
            "existing_risk_report_modified": report[
                "existing_risk_report_modified"
            ],
        })

        for population, result in report["populations"].items():
            prefix = population

            for section in ("training", "evaluation"):
                mlflow.log_metric(
                    f"{prefix}_{section}_rows",
                    result[section]["rows"],
                )

            evaluation = result["evaluation"]
            log_metric_if_valid(
                f"{prefix}_anomaly_rate_pct",
                evaluation["anomaly_percentage"],
            )
            log_metric_if_valid(
                f"{prefix}_anomaly_count",
                evaluation["anomaly_count"],
            )
            log_metric_if_valid(
                f"{prefix}_threshold",
                evaluation["threshold"],
            )

            shift = result["score_distribution_shift"]
            for metric_name, value in shift.items():
                log_metric_if_valid(
                    f"{prefix}_score_{metric_name}",
                    value,
                )

            drift = result["continuous_feature_drift"]
            log_metric_if_valid(
                f"{prefix}_continuous_mean_psi",
                drift["mean_psi"],
            )

            timeline = result["evaluation"]["timeline"]
            log_metric_if_valid(
                f"{prefix}_evaluation_active_days",
                timeline["active_calendar_days"],
            )
            log_metric_if_valid(
                f"{prefix}_max_rolling_5min_events",
                timeline["maximum_rolling_5min_events"],
            )

            for window in evaluation["windows"]:
                window_id = window["window"]
                log_metric_if_valid(
                    f"{prefix}_window_{window_id}_rows",
                    window["rows"],
                )
                log_metric_if_valid(
                    f"{prefix}_window_{window_id}_anomaly_pct",
                    window["anomaly_percentage"],
                )

        mlflow.log_artifact(str(REPORT_PATH), artifact_path="reports")

        if SCRIPT_PATH.exists():
            mlflow.log_artifact(str(SCRIPT_PATH), artifact_path="source")

        print("MLflow run completed.")
        print("Experiment:", EXPERIMENT_NAME)
        print("Run ID:", mlflow.active_run().info.run_id)
        print("Dataset SHA-256:", dataset_hash)
        print("Dataset rows:", dataset_rows)
        print("Tracking database:", TRACKING_DB.resolve())


if __name__ == "__main__":
    main()
