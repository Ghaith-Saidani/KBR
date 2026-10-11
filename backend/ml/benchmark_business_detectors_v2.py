from __future__ import annotations
import os

import hashlib
import json
import time
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
REPORT_PATH = ROOT / "data" / "reports" / "business_detector_benchmark_v2.json"
MLFLOW_DB = ROOT / "mlflow.db"

EXPERIMENT_NAME = "KBR-Anomaly-Detection"
SESSION_GAP_MINUTES = 1
TRAIN_FRACTION = 0.80
THRESHOLD_QUANTILE = 0.95
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "gap_log_seconds",
    "events_previous_5m",
    "events_previous_1h",
]

CATEGORICAL_FEATURES = [
    "action",
    "method",
    "resource_type",
]


def find_column(df: pd.DataFrame, candidates: list[str]) -> str:
    """Find a column using case-insensitive candidate names."""
    lookup = {str(col).strip().lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    raise ValueError(
        f"Could not find any of {candidates}. "
        f"Available columns: {list(df.columns)}"
    )


def dataset_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def quantiles(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=float)

    return {
        "median": float(np.quantile(values, 0.50)),
        "p90": float(np.quantile(values, 0.90)),
        "p95": float(np.quantile(values, 0.95)),
        "p99": float(np.quantile(values, 0.99)),
    }


def summarize_detector(
    train_scores: np.ndarray,
    eval_scores: np.ndarray,
    threshold: float,
    higher_is_anomalous: bool = True,
) -> dict:
    if higher_is_anomalous:
        flags = eval_scores > threshold
    else:
        flags = eval_scores < threshold

    count = int(flags.sum())
    total = int(len(flags))

    return {
        "threshold": float(threshold),
        "training_score_quantiles": quantiles(train_scores),
        "evaluation_score_quantiles": quantiles(eval_scores),
        "evaluation_anomaly_count": count,
        "evaluation_rows": total,
        "evaluation_anomaly_rate_pct": (
            float(count / total * 100) if total else 0.0
        ),
    }


def build_business_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    timestamp_col = find_column(
        raw,
        ["timestamp", "created_at", "event_timestamp", "datetime", "time"],
    )

    timestamp = pd.to_datetime(
        raw[timestamp_col],
        format="mixed",
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = int(timestamp.isna().sum())

    df = raw.loc[timestamp.notna()].copy()
    df["_timestamp"] = timestamp.loc[timestamp.notna()]
    df = df.sort_values("_timestamp", kind="stable").reset_index(drop=True)

    # Identify the business population without assuming a specific schema.
    population_col = next(
        (
            col for col in df.columns
            if str(col).strip().lower()
            in {"population", "event_population", "traffic_type", "source_type"}
        ),
        None,
    )

    if population_col is not None:
        values = df[population_col].astype(str).str.lower()
        business_mask = values.str.contains(
            r"business|application|domain", regex=True, na=False
        )
        http_mask = values.str.contains(
            r"http|request|web", regex=True, na=False
        )

        if business_mask.any() and http_mask.any():
            df = df.loc[business_mask].copy()

    # If a population column was not usable, use the known event-type field
    # where available. Otherwise retain the dataset and report the limitation.
    event_type_col = next(
        (
            col for col in df.columns
            if str(col).strip().lower()
            in {"event_type", "type", "category", "log_type"}
        ),
        None,
    )

    if event_type_col is not None:
        values = df[event_type_col].astype(str).str.lower()
        if values.str.contains(r"\bhttp\b|request|response", regex=True).any():
            business_mask = values.str.contains(
                r"business|application|domain", regex=True, na=False
            )
            if business_mask.any():
                df = df.loc[business_mask].copy()

    if df.empty:
        raise ValueError("No business records remained after population filtering.")

    action_col = find_column(
        df, ["action", "activity", "event_name", "operation", "event"]
    )

    method_col = next(
        (
            col for col in df.columns
            if str(col).strip().lower() in {"method", "http_method"}
        ),
        None,
    )

    resource_col = next(
        (
            col for col in df.columns
            if str(col).strip().lower()
            in {"resource_type", "resource", "entity_type", "object_type"}
        ),
        None,
    )

    # Some business datasets have no HTTP method; represent missing values
    # explicitly rather than silently dropping rows.
    df["action"] = df[action_col].fillna("<missing>").astype(str)
    df["method"] = (
        df[method_col].fillna("<missing>").astype(str)
        if method_col
        else "<not_applicable>"
    )
    df["resource_type"] = (
        df[resource_col].fillna("<missing>").astype(str)
        if resource_col
        else "<not_available>"
    )

    return df.reset_index(drop=True), {
        "timestamp_column": str(timestamp_col),
        "invalid_timestamp_rows": invalid_timestamps,
        "population_column": str(population_col) if population_col else None,
        "action_column": str(action_col),
        "method_column": str(method_col) if method_col else None,
        "resource_type_column": str(resource_col) if resource_col else None,
    }


def add_causal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate rolling activity features using only previous events."""
    result = df.copy()
    timestamps = result["_timestamp"]

    gap_seconds = timestamps.diff().dt.total_seconds()
    result["gap_log_seconds"] = np.log1p(gap_seconds.clip(lower=0).fillna(0))

    indexed = pd.Series(
        np.ones(len(result), dtype=float),
        index=pd.DatetimeIndex(timestamps),
    )

    # The rolling windows are shifted so the current event is not counted
    # in its own historical activity features.
    previous_5m = (
        indexed.rolling("5min", closed="left").sum().to_numpy()
    )
    previous_1h = (
        indexed.rolling("1h", closed="left").sum().to_numpy()
    )

    result["events_previous_5m"] = np.nan_to_num(previous_5m, nan=0.0)
    result["events_previous_1h"] = np.nan_to_num(previous_1h, nan=0.0)

    # Group sessions using a one-minute inactivity gap.
    gap = timestamps.diff().dt.total_seconds().fillna(float("inf"))
    result["session_id"] = (
        gap.gt(SESSION_GAP_MINUTES * 60).cumsum().astype(int)
    )

    # A stable session-level chronological holdout prevents sessions from
    # being split between training and evaluation.
    return result


def build_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sessions = (
        df.groupby("session_id", sort=False)["_timestamp"]
        .agg(start="min", end="max", rows="size")
        .sort_values("start")
    )

    if len(sessions) < 5:
        raise ValueError(
            f"Only {len(sessions)} sessions available; insufficient for "
            "an 80/20 chronological session split."
        )

    split_index = int(len(sessions) * TRAIN_FRACTION)
    split_index = min(max(split_index, 1), len(sessions) - 1)

    train_ids = set(sessions.index[:split_index])
    eval_ids = set(sessions.index[split_index:])

    train = df[df["session_id"].isin(train_ids)].copy()
    evaluation = df[df["session_id"].isin(eval_ids)].copy()

    if set(train["session_id"]) & set(evaluation["session_id"]):
        raise RuntimeError("Session leakage detected between train and evaluation.")

    if train.empty or evaluation.empty:
        raise ValueError("Training or evaluation split is empty.")

    return train, evaluation


def robust_baseline(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Robust score based only on event gaps and previous activity counts.

    Uses median and MAD-derived scales, with IQR and standard-deviation
    fallbacks to avoid division by zero or near-zero variation.
    """
    medians: dict[str, float] = {}
    scales: dict[str, float] = {}

    train_matrix = train[NUMERIC_FEATURES].astype(float)
    eval_matrix = evaluation[NUMERIC_FEATURES].astype(float)

    for feature in NUMERIC_FEATURES:
        values = train_matrix[feature].to_numpy()
        median = float(np.median(values))
        mad_scale = float(1.4826 * np.median(np.abs(values - median)))
        iqr_scale = float(
            (np.quantile(values, 0.75) - np.quantile(values, 0.25)) / 1.349
        )
        std_scale = float(np.std(values))

        # Scale floor is only a numerical safeguard; it avoids huge scores
        # when a feature is almost constant in the training data.
        scale = max(mad_scale, iqr_scale, std_scale, 1e-6)

        medians[feature] = median
        scales[feature] = scale

    def score(frame: pd.DataFrame) -> np.ndarray:
        matrix = frame[NUMERIC_FEATURES].astype(float).to_numpy()
        centers = np.array([medians[f] for f in NUMERIC_FEATURES])
        feature_scales = np.array([scales[f] for f in NUMERIC_FEATURES])

        z_scores = np.abs((matrix - centers) / feature_scales)
        return np.max(z_scores, axis=1)

    train_scores = score(train)
    eval_scores = score(evaluation)

    return train_scores, eval_scores, {
        "features": NUMERIC_FEATURES,
        "feature_medians": medians,
        "feature_scales": scales,
        "scaling": "max absolute robust z-score; MAD/IQR/std fallback",
    }


def categorical_diagnostics(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
) -> dict:
    result = {}

    for feature in CATEGORICAL_FEATURES:
        train_values = set(train[feature].astype(str))
        eval_values = evaluation[feature].astype(str)
        unseen_mask = ~eval_values.isin(train_values)

        result[feature] = {
            "training_unique_values": int(len(train_values)),
            "evaluation_unique_values": int(eval_values.nunique()),
            "evaluation_unseen_rows": int(unseen_mask.sum()),
            "evaluation_unseen_rate_pct": float(unseen_mask.mean() * 100),
        }

    return result


def main() -> None:
    started = time.perf_counter()

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    raw = pd.read_csv(DATASET_PATH)
    dataset_hash = dataset_sha256(DATASET_PATH)

    business, schema = build_business_dataset(raw)
    business = add_causal_features(business)
    train, evaluation = build_split(business)

    # Isolation Forest comparison.
    forest_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    train_encoded = pd.get_dummies(
        train[forest_features].astype({feature: str for feature in CATEGORICAL_FEATURES}),
        columns=CATEGORICAL_FEATURES,
        dtype=float,
    )
    eval_encoded = pd.get_dummies(
        evaluation[forest_features].astype({feature: str for feature in CATEGORICAL_FEATURES}),
        columns=CATEGORICAL_FEATURES,
        dtype=float,
    )
    eval_encoded = eval_encoded.reindex(
        columns=train_encoded.columns, fill_value=0
    )

    forest = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    fit_started = time.perf_counter()
    forest.fit(train_encoded)
    forest_fit_seconds = time.perf_counter() - fit_started

    # sklearn decision_function: lower scores are more anomalous.
    forest_train_scores = forest.decision_function(train_encoded)
    forest_eval_scores = forest.decision_function(eval_encoded)
    forest_threshold = float(
        np.quantile(forest_train_scores, 1 - THRESHOLD_QUANTILE)
    )

    forest_report = summarize_detector(
        forest_train_scores,
        forest_eval_scores,
        forest_threshold,
        higher_is_anomalous=False,
    )
    forest_report["detector"] = "IsolationForest"
    forest_report["training_runtime_seconds"] = forest_fit_seconds

    # Robust statistical baseline: no calendar sine/cosine features.
    baseline_train_scores, baseline_eval_scores, scaling = robust_baseline(
        train, evaluation
    )
    baseline_threshold = float(
        np.quantile(baseline_train_scores, THRESHOLD_QUANTILE)
    )

    baseline_report = summarize_detector(
        baseline_train_scores,
        baseline_eval_scores,
        baseline_threshold,
        higher_is_anomalous=True,
    )
    baseline_report["detector"] = "RobustStatisticalBaselineV2"

    split_report = {
        "total_sessions": int(business["session_id"].nunique()),
        "training_sessions": int(train["session_id"].nunique()),
        "evaluation_sessions": int(evaluation["session_id"].nunique()),
        "training_rows": int(len(train)),
        "evaluation_rows": int(len(evaluation)),
        "training_active_days": int(train["_timestamp"].dt.date.nunique()),
        "evaluation_active_days": int(
            evaluation["_timestamp"].dt.date.nunique()
        ),
        "training_start": train["_timestamp"].min().isoformat(),
        "training_end": train["_timestamp"].max().isoformat(),
        "evaluation_start": evaluation["_timestamp"].min().isoformat(),
        "evaluation_end": evaluation["_timestamp"].max().isoformat(),
        "sessions_crossing_split": 0,
    }

    report = {
        "report_version": 2,
        "experiment": EXPERIMENT_NAME,
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "dataset_sha256": dataset_hash,
        "original_dataset_rows": int(len(raw)),
        "business_rows": int(len(business)),
        "schema": schema,
        "evaluation_method": (
            "Chronological session holdout; one-minute inactivity gap."
        ),
        "session_gap_minutes": SESSION_GAP_MINUTES,
        "training_session_fraction": TRAIN_FRACTION,
        "anomaly_threshold_quantile": THRESHOLD_QUANTILE,
        "labels_available": False,
        "accuracy_metrics_available": False,
        "interpretation": (
            "Exploratory detector comparison only. No labels are available, "
            "so anomaly rates are not precision, recall, F1, or evidence of "
            "true incidents. Evaluation coverage and distribution shift must "
            "be considered before choosing a detector."
        ),
        "split": split_report,
        "detectors": {
            "isolation_forest": forest_report,
            "robust_statistical_baseline_v2": baseline_report,
        },
        "baseline_v2_scaling": scaling,
        "categorical_unseen_values": categorical_diagnostics(train, evaluation),
        "saved_models_modified": False,
        "existing_risk_report_modified": False,
    }

    report["total_runtime_seconds"] = time.perf_counter() - started

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    mlflow.set_tracking_uri(
        os.getenv("MLFLOW_TRACKING_URI")
        or f"sqlite:///{MLFLOW_DB.as_posix()}"
    )
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="business-detector-benchmark-v2") as run:
        mlflow.set_tags(
            {
                "benchmark_version": "2",
                "dataset_sha256": dataset_hash,
                "population": "business",
                "production_model_modified": "false",
            }
        )

        mlflow.log_params(
            {
                "session_gap_minutes": SESSION_GAP_MINUTES,
                "training_session_fraction": TRAIN_FRACTION,
                "threshold_quantile": THRESHOLD_QUANTILE,
                "isolation_forest_estimators": 300,
                "baseline_features": ",".join(NUMERIC_FEATURES),
                "calendar_features_excluded_from_baseline": True,
                "random_state": RANDOM_STATE,
            }
        )

        mlflow.log_metrics(
            {
                "business_rows": len(business),
                "training_rows": len(train),
                "evaluation_rows": len(evaluation),
                "training_sessions": train["session_id"].nunique(),
                "evaluation_sessions": evaluation["session_id"].nunique(),
                "forest_anomaly_rate_pct": forest_report[
                    "evaluation_anomaly_rate_pct"
                ],
                "baseline_v2_anomaly_rate_pct": baseline_report[
                    "evaluation_anomaly_rate_pct"
                ],
                "forest_threshold": forest_threshold,
                "baseline_v2_threshold": baseline_threshold,
                "total_runtime_seconds": report["total_runtime_seconds"],
            }
        )

        mlflow.log_artifact(str(REPORT_PATH), artifact_path="reports")

        report["mlflow_run_id"] = run.info.run_id

    # Update report with the MLflow run ID after the run has finished.
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Report: {REPORT_PATH}")
    print(f"Dataset SHA-256: {dataset_hash}")
    print(f"MLflow run ID: {report['mlflow_run_id']}")
    print(f"Business rows: {len(business)}")
    print(f"Training rows: {len(train)}")
    print(f"Evaluation rows: {len(evaluation)}")
    print(
        "Isolation Forest anomalies: "
        f"{forest_report['evaluation_anomaly_count']}/"
        f"{forest_report['evaluation_rows']} "
        f"({forest_report['evaluation_anomaly_rate_pct']:.2f}%)"
    )
    print(
        "Baseline v2 anomalies: "
        f"{baseline_report['evaluation_anomaly_count']}/"
        f"{baseline_report['evaluation_rows']} "
        f"({baseline_report['evaluation_anomaly_rate_pct']:.2f}%)"
    )
    print("Production models and the existing risk report were not modified.")


if __name__ == "__main__":
    main()