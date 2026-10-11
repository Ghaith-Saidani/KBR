from __future__ import annotations
import os

import hashlib
import json
import time
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATASET_PATH = Path("data/processed/user_activities.csv")
REPORT_PATH = Path("data/reports/business_detector_benchmark.json")
TRACKING_DB = Path("mlflow.db")

EXPERIMENT_NAME = "KBR-Anomaly-Detection"
SESSION_GAP_MINUTES = 1
TRAIN_SESSION_FRACTION = 0.80
ANOMALY_QUANTILE = 0.95
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "gap_log_seconds",
    "events_previous_5m",
    "events_previous_1h",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
]

CATEGORICAL_FEATURES = [
    "action",
    "method",
    "resource_type",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def make_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build causal per-event features without using future events."""
    result = frame.sort_values("occurred_at").copy()
    timestamps = result["occurred_at"]

    gaps = timestamps.diff().dt.total_seconds()
    result["gap_log_seconds"] = np.log1p(
        gaps.clip(lower=0).fillna(0)
    )

    indexed_ones = pd.Series(
        1.0,
        index=pd.DatetimeIndex(timestamps),
    )

    result["events_previous_5m"] = (
        indexed_ones
        .rolling("5min", closed="left")
        .sum()
        .fillna(0)
        .to_numpy()
    )

    result["events_previous_1h"] = (
        indexed_ones
        .rolling("1h", closed="left")
        .sum()
        .fillna(0)
        .to_numpy()
    )

    hour = (
        timestamps.dt.hour
        + timestamps.dt.minute / 60.0
        + timestamps.dt.second / 3600.0
    )
    weekday = timestamps.dt.dayofweek

    result["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    result["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    result["weekday_sin"] = np.sin(2 * np.pi * weekday / 7)
    result["weekday_cos"] = np.cos(2 * np.pi * weekday / 7)

    for column in CATEGORICAL_FEATURES:
        if column not in result.columns:
            result[column] = "__MISSING__"
        result[column] = (
            result[column]
            .fillna("__MISSING__")
            .astype(str)
        )

    result[NUMERIC_FEATURES] = (
        result[NUMERIC_FEATURES]
        .replace([np.inf, -np.inf], np.nan)
    )

    return result


def assign_sessions(
    frame: pd.DataFrame,
    gap_minutes: int,
) -> pd.DataFrame:
    result = frame.sort_values("occurred_at").copy()
    gaps = result["occurred_at"].diff()

    new_session = gaps.isna() | (
        gaps > pd.Timedelta(minutes=int(gap_minutes))
    )
    result["session_id"] = new_session.cumsum().astype(int)

    return result


def robust_baseline_scores(
    train_numeric: pd.DataFrame,
    evaluation_numeric: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Maximum robust z-score, calibrated only on training data."""
    train_values = train_numeric.to_numpy(dtype=float)
    evaluation_values = evaluation_numeric.to_numpy(dtype=float)

    medians = np.nanmedian(train_values, axis=0)
    deviations = np.nanmedian(
        np.abs(train_values - medians),
        axis=0,
    )

    scales = deviations * 1.4826

    # Fall back to standard deviation for zero-MAD features.
    standard_deviations = np.nanstd(train_values, axis=0)
    scales = np.where(
        scales > 1e-9,
        scales,
        standard_deviations,
    )
    scales = np.where(scales > 1e-9, scales, 1.0)

    train_z = np.abs((train_values - medians) / scales)
    evaluation_z = np.abs(
        (evaluation_values - medians) / scales
    )

    train_scores = np.nanmax(train_z, axis=1)
    evaluation_scores = np.nanmax(evaluation_z, axis=1)

    details = {
        "feature_medians": dict(zip(NUMERIC_FEATURES, medians)),
        "feature_scales": dict(zip(NUMERIC_FEATURES, scales)),
    }

    return train_scores, evaluation_scores, details


def numeric_psi(
    training: pd.Series,
    evaluation: pd.Series,
    bins: int = 10,
) -> float:
    """Population Stability Index using training quantile boundaries."""
    train = training.dropna().to_numpy(dtype=float)
    evaluation = evaluation.dropna().to_numpy(dtype=float)

    if len(train) == 0 or len(evaluation) == 0:
        return float("nan")

    quantiles = np.linspace(0, 1, bins + 1)
    inner_edges = np.unique(np.quantile(train, quantiles))
    edges = np.unique(
        np.concatenate(([-np.inf], inner_edges, [np.inf]))
    )

    train_counts, _ = np.histogram(train, bins=edges)
    eval_counts, _ = np.histogram(evaluation, bins=edges)

    train_share = np.maximum(
        train_counts / len(train), 1e-6
    )
    eval_share = np.maximum(
        eval_counts / len(evaluation), 1e-6
    )

    return float(
        np.sum(
            (eval_share - train_share)
            * np.log(eval_share / train_share)
        )
    )


def score_summary(
    train_scores: np.ndarray,
    evaluation_scores: np.ndarray,
    name: str,
) -> dict:
    threshold = float(
        np.quantile(train_scores, ANOMALY_QUANTILE)
    )
    flags = evaluation_scores > threshold

    return {
        "detector": name,
        "threshold": threshold,
        "training_score_quantiles": {
            "median": float(np.quantile(train_scores, 0.50)),
            "p90": float(np.quantile(train_scores, 0.90)),
            "p95": float(np.quantile(train_scores, 0.95)),
            "p99": float(np.quantile(train_scores, 0.99)),
        },
        "evaluation_score_quantiles": {
            "median": float(np.quantile(evaluation_scores, 0.50)),
            "p90": float(np.quantile(evaluation_scores, 0.90)),
            "p95": float(np.quantile(evaluation_scores, 0.95)),
            "p99": float(np.quantile(evaluation_scores, 0.99)),
        },
        "evaluation_anomaly_count": int(flags.sum()),
        "evaluation_rows": int(len(flags)),
        "evaluation_anomaly_rate_pct": float(
            flags.mean() * 100
        ),
    }


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH.resolve()}"
        )

    started = time.perf_counter()
    raw = pd.read_csv(DATASET_PATH)
    original_rows = len(raw)

    required = {
        "occurred_at",
        "resource_type",
        "action",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {sorted(missing)}"
        )

    raw["occurred_at"] = pd.to_datetime(
        raw["occurred_at"],
        format="mixed",
        errors="coerce",
        utc=True,
    )
    invalid_timestamps = int(raw["occurred_at"].isna().sum())
    raw = raw.dropna(subset=["occurred_at"]).copy()

    # Business population only. HTTP model is not evaluated here.
    business = raw[
        raw["resource_type"].ne("http_request")
    ].copy()

    if business.empty:
        raise ValueError("No business activity rows were found.")

    business = assign_sessions(
        business,
        SESSION_GAP_MINUTES,
    )

    session_table = (
        business.groupby("session_id", sort=True)
        .agg(
            start=("occurred_at", "min"),
            end=("occurred_at", "max"),
            rows=("occurred_at", "size"),
        )
        .reset_index()
    )

    if len(session_table) < 5:
        raise ValueError(
            "Too few sessions to run the exploratory benchmark."
        )

    split_index = int(
        len(session_table) * TRAIN_SESSION_FRACTION
    )
    split_index = max(1, min(split_index, len(session_table) - 1))

    training_session_ids = set(
        session_table.iloc[:split_index]["session_id"]
    )
    evaluation_session_ids = set(
        session_table.iloc[split_index:]["session_id"]
    )

    # Feature creation uses only present and past timestamps.
    featured = make_features(business)

    training = featured[
        featured["session_id"].isin(training_session_ids)
    ].copy()
    evaluation = featured[
        featured["session_id"].isin(evaluation_session_ids)
    ].copy()

    if training.empty or evaluation.empty:
        raise ValueError("Training or evaluation partition is empty.")

    X_train_numeric = training[NUMERIC_FEATURES].copy()
    X_eval_numeric = evaluation[NUMERIC_FEATURES].copy()

    X_train = training[
        NUMERIC_FEATURES + CATEGORICAL_FEATURES
    ].copy()
    X_eval = evaluation[
        NUMERIC_FEATURES + CATEGORICAL_FEATURES
    ].copy()

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(
                strategy="constant",
                fill_value="__MISSING__",
            ),
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
                min_frequency=2,
            ),
        ),
    ])

    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])

    forest = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("detector", forest),
    ])

    model_started = time.perf_counter()
    model.fit(X_train)
    training_seconds = time.perf_counter() - model_started

    # Higher scores mean more anomalous for both detectors.
    forest_train_scores = -model.decision_function(X_train)
    forest_eval_scores = -model.decision_function(X_eval)

    baseline_train_scores, baseline_eval_scores, baseline_details = (
        robust_baseline_scores(
            X_train_numeric,
            X_eval_numeric,
        )
    )

    forest_result = score_summary(
        forest_train_scores,
        forest_eval_scores,
        "IsolationForest",
    )
    baseline_result = score_summary(
        baseline_train_scores,
        baseline_eval_scores,
        "RobustStatisticalBaseline",
    )

    drift = {}
    for column in NUMERIC_FEATURES:
        drift[column] = numeric_psi(
            X_train_numeric[column],
            X_eval_numeric[column],
        )

    unseen_categories = {}
    for column in CATEGORICAL_FEATURES:
        train_values = set(training[column].astype(str))
        eval_values = evaluation[column].astype(str)

        unseen_categories[column] = {
            "training_unique_values": len(train_values),
            "evaluation_unique_values": int(
                eval_values.nunique()
            ),
            "evaluation_unseen_rows": int(
                (~eval_values.isin(train_values)).sum()
            ),
            "evaluation_unseen_rate_pct": float(
                (~eval_values.isin(train_values)).mean() * 100
            ),
        }

    evaluation_details = evaluation[
        ["session_id", "occurred_at"]
    ].copy()
    evaluation_details["forest_score"] = forest_eval_scores
    evaluation_details["forest_anomaly"] = (
        forest_eval_scores > forest_result["threshold"]
    )
    evaluation_details["baseline_score"] = baseline_eval_scores
    evaluation_details["baseline_anomaly"] = (
        baseline_eval_scores > baseline_result["threshold"]
    )

    session_metrics = (
        evaluation_details.groupby("session_id")
        .agg(
            rows=("occurred_at", "size"),
            start=("occurred_at", "min"),
            end=("occurred_at", "max"),
            forest_anomalies=("forest_anomaly", "sum"),
            baseline_anomalies=("baseline_anomaly", "sum"),
            forest_max_score=("forest_score", "max"),
            baseline_max_score=("baseline_score", "max"),
        )
        .reset_index()
    )

    session_metrics["duration_seconds"] = (
        session_metrics["end"] - session_metrics["start"]
    ).dt.total_seconds()

    session_metrics["forest_anomaly_rate_pct"] = (
        session_metrics["forest_anomalies"]
        / session_metrics["rows"] * 100
    )
    session_metrics["baseline_anomaly_rate_pct"] = (
        session_metrics["baseline_anomalies"]
        / session_metrics["rows"] * 100
    )

    top_sessions = (
        session_metrics.sort_values("rows", ascending=False)
        .head(20)
        .copy()
    )
    top_sessions["start"] = top_sessions["start"].astype(str)
    top_sessions["end"] = top_sessions["end"].astype(str)

    dataset_hash = sha256_file(DATASET_PATH)
    evaluation_days = int(
        evaluation["occurred_at"].dt.normalize().nunique()
    )

    report = {
        "report_version": 1,
        "experiment": EXPERIMENT_NAME,
        "dataset": str(DATASET_PATH),
        "dataset_sha256": dataset_hash,
        "original_dataset_rows": original_rows,
        "invalid_timestamp_rows": invalid_timestamps,
        "business_rows": len(business),
        "http_rows_excluded": int(
            raw["resource_type"].eq("http_request").sum()
        ),
        "evaluation_method": (
            "Chronological session holdout; session boundaries are "
            "defined by a one-minute inactivity gap."
        ),
        "session_gap_minutes": SESSION_GAP_MINUTES,
        "training_session_fraction": TRAIN_SESSION_FRACTION,
        "anomaly_threshold_quantile": ANOMALY_QUANTILE,
        "labels_available": False,
        "accuracy_metrics_available": False,
        "interpretation": (
            "Exploratory detector-behavior comparison only. No labels "
            "are available, so anomaly rates are not precision, recall, "
            "F1, or evidence that flagged events are true incidents. "
            "The evaluation is concentrated in a small number of active "
            "days and may not represent future traffic."
        ),
        "split": {
            "total_sessions": len(session_table),
            "training_sessions": len(training_session_ids),
            "evaluation_sessions": len(evaluation_session_ids),
            "training_rows": len(training),
            "evaluation_rows": len(evaluation),
            "training_active_days": int(
                training["occurred_at"].dt.normalize().nunique()
            ),
            "evaluation_active_days": evaluation_days,
            "training_start": str(training["occurred_at"].min()),
            "training_end": str(training["occurred_at"].max()),
            "evaluation_start": str(evaluation["occurred_at"].min()),
            "evaluation_end": str(evaluation["occurred_at"].max()),
            "sessions_crossing_split": len(
                training_session_ids.intersection(
                    evaluation_session_ids
                )
            ),
        },
        "detectors": {
            "isolation_forest": forest_result,
            "robust_statistical_baseline": baseline_result,
        },
        "numeric_feature_psi": drift,
        "mean_numeric_psi": float(np.nanmean(list(drift.values()))),
        "categorical_unseen_values": unseen_categories,
        "training_runtime_seconds": training_seconds,
        "total_runtime_seconds": time.perf_counter() - started,
        "baseline_robust_scaling": baseline_details,
        "evaluation_session_summary": {
            "evaluation_sessions": len(session_metrics),
            "sessions_with_forest_flags": int(
                (session_metrics["forest_anomalies"] > 0).sum()
            ),
            "sessions_with_baseline_flags": int(
                (session_metrics["baseline_anomalies"] > 0).sum()
            ),
            "largest_evaluation_sessions": top_sessions.to_dict(
                orient="records"
            ),
        },
        "saved_models_modified": False,
        "existing_risk_report_modified": False,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(json_safe(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Log to the existing SQLite-backed MLflow experiment.
    mlflow.set_tracking_uri(
        os.getenv("MLFLOW_TRACKING_URI")
        or f"sqlite:///{TRACKING_DB.resolve().as_posix()}"
    )
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(
        run_name="business-session-detector-benchmark"
    ):
        mlflow.set_tags({
            "project": "KBR",
            "task": "business-anomaly-detection",
            "evaluation_type": "chronological-session-holdout",
            "labels_available": "false",
            "models_saved": "false",
            "production_models_modified": "false",
        })

        mlflow.log_params({
            "dataset_sha256": dataset_hash,
            "dataset_rows": len(raw),
            "business_rows": len(business),
            "session_gap_minutes": SESSION_GAP_MINUTES,
            "training_session_fraction": TRAIN_SESSION_FRACTION,
            "anomaly_threshold_quantile": ANOMALY_QUANTILE,
            "isolation_forest_estimators": 300,
            "random_state": RANDOM_STATE,
            "sklearn_version": sklearn.__version__,
        })

        mlflow.log_metrics({
            "training_rows": len(training),
            "evaluation_rows": len(evaluation),
            "training_sessions": len(training_session_ids),
            "evaluation_sessions": len(evaluation_session_ids),
            "training_active_days": report["split"]["training_active_days"],
            "evaluation_active_days": evaluation_days,
            "mean_numeric_psi": report["mean_numeric_psi"],
            "training_runtime_seconds": training_seconds,
            "total_runtime_seconds": report["total_runtime_seconds"],
            "forest_threshold": forest_result["threshold"],
            "forest_eval_anomaly_rate_pct":
                forest_result["evaluation_anomaly_rate_pct"],
            "forest_eval_anomaly_count":
                forest_result["evaluation_anomaly_count"],
            "baseline_threshold": baseline_result["threshold"],
            "baseline_eval_anomaly_rate_pct":
                baseline_result["evaluation_anomaly_rate_pct"],
            "baseline_eval_anomaly_count":
                baseline_result["evaluation_anomaly_count"],
        })

        for feature, value in drift.items():
            if np.isfinite(value):
                mlflow.log_metric(f"psi_{feature}", float(value))

        for column, details in unseen_categories.items():
            mlflow.log_metric(
                f"unseen_rate_pct_{column}",
                details["evaluation_unseen_rate_pct"],
            )

        mlflow.log_artifact(
            str(REPORT_PATH),
            artifact_path="reports",
        )

        script_path = Path("backend/ml/benchmark_business_detectors.py")
        if script_path.exists():
            mlflow.log_artifact(str(script_path), artifact_path="source")

        run_id = mlflow.active_run().info.run_id

    print("\n=== BUSINESS DETECTOR BENCHMARK ===")
    print(f"Dataset SHA-256: {dataset_hash}")
    print(f"Business rows: {len(business)}")
    print(
        f"Split: {len(training_session_ids)} train sessions / "
        f"{len(evaluation_session_ids)} evaluation sessions"
    )
    print(f"Rows: {len(training)} train / {len(evaluation)} evaluation")
    print(
        f"Active days: {report['split']['training_active_days']} train / "
        f"{evaluation_days} evaluation"
    )

    for result in (forest_result, baseline_result):
        print(f"\n{result['detector']}")
        print(f"  Threshold: {result['threshold']:.6f}")
        print(
            f"  Evaluation anomalies: "
            f"{result['evaluation_anomaly_count']} / "
            f"{result['evaluation_rows']}"
        )
        print(
            f"  Evaluation anomaly rate: "
            f"{result['evaluation_anomaly_rate_pct']:.2f}%"
        )

    print(f"\nMean numeric PSI: {report['mean_numeric_psi']:.4f}")
    print("Labels available: no")
    print("Accuracy metrics: not calculated")
    print(f"MLflow run ID: {run_id}")
    print(f"Report: {REPORT_PATH.resolve()}")
    print("Saved models and existing risk report were not modified.")


if __name__ == "__main__":
    main()
