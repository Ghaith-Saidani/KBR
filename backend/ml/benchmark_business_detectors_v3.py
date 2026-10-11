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
REPORT_PATH = ROOT / "data" / "reports" / "business_detector_benchmark_v3.json"
MLFLOW_DB = ROOT / "mlflow.db"

EXPERIMENT_NAME = "KBR-Anomaly-Detection"
RANDOM_STATE = 42
TRAIN_FRACTION = 0.80
THRESHOLDS = (0.01, 0.02, 0.05)
SESSION_GAPS_MINUTES = (1, 5, 15)

NUMERIC_FEATURES = [
    "gap_log_seconds",
    "events_previous_5m",
    "events_previous_1h",
]
CATEGORICAL_FEATURES = ["action", "method", "resource_type"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_column(df: pd.DataFrame, candidates: list[str]) -> str:
    lookup = {str(column).strip().lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    raise ValueError(
        f"Could not find a column among {candidates}. "
        f"Available columns: {list(df.columns)}"
    )


def load_business_data() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(DATASET_PATH)

    timestamp_column = find_column(
        raw, ["occurred_at", "timestamp", "created_at", "event_timestamp", "datetime"]
    )
    parsed = pd.to_datetime(
        raw[timestamp_column], format="mixed", errors="coerce", utc=True
    )
    invalid_timestamps = int(parsed.isna().sum())

    df = raw.loc[parsed.notna()].copy()
    df["_timestamp"] = parsed.loc[parsed.notna()]
    df = df.sort_values("_timestamp", kind="stable").reset_index(drop=True)

    # Use an explicit population column if one exists and distinguishes
    # business and HTTP events. Otherwise preserve all rows in the supplied
    # activity dataset, as in the previous v2 benchmark.
    population_column = next(
        (
            col for col in df.columns
            if str(col).strip().lower()
            in {"population", "event_population", "traffic_type", "source_type"}
        ),
        None,
    )

    if population_column is not None:
        values = df[population_column].astype(str).str.lower()
        business_mask = values.str.contains(
            r"business|application|domain", regex=True, na=False
        )
        http_mask = values.str.contains(
            r"http|request|web", regex=True, na=False
        )
        if business_mask.any() and http_mask.any():
            df = df.loc[business_mask].copy()

    action_column = find_column(
        df, ["action", "activity", "event_name", "operation", "event"]
    )

    method_column = next(
        (
            col for col in df.columns
            if str(col).strip().lower() in {"method", "http_method"}
        ),
        None,
    )
    resource_column = next(
        (
            col for col in df.columns
            if str(col).strip().lower()
            in {"resource_type", "resource", "entity_type", "object_type"}
        ),
        None,
    )

    df["action"] = df[action_column].fillna("<missing>").astype(str)
    df["method"] = (
        df[method_column].fillna("<missing>").astype(str)
        if method_column else "<not_applicable>"
    )
    df["resource_type"] = (
        df[resource_column].fillna("<missing>").astype(str)
        if resource_column else "<not_available>"
    )

    if df.empty:
        raise ValueError("No usable rows remain after timestamp parsing.")

    schema = {
        "timestamp_column": str(timestamp_column),
        "invalid_timestamp_rows": invalid_timestamps,
        "population_column": (
            str(population_column) if population_column else None
        ),
        "action_column": str(action_column),
        "method_column": str(method_column) if method_column else None,
        "resource_type_column": (
            str(resource_column) if resource_column else None
        ),
    }
    return df.reset_index(drop=True), schema


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    timestamps = result["_timestamp"]

    gap_seconds = timestamps.diff().dt.total_seconds()
    result["gap_log_seconds"] = np.log1p(
        gap_seconds.clip(lower=0).fillna(0)
    )

    # Count earlier events only; do not include the current event in its
    # own rolling features.
    time_index = pd.DatetimeIndex(timestamps)
    event_series = pd.Series(
        np.ones(len(result), dtype=float), index=time_index
    )
    result["events_previous_5m"] = np.nan_to_num(
        event_series.rolling("5min", closed="left").sum().to_numpy(),
        nan=0.0,
    )
    result["events_previous_1h"] = np.nan_to_num(
        event_series.rolling("1h", closed="left").sum().to_numpy(),
        nan=0.0,
    )
    return result


def assign_sessions(
    df: pd.DataFrame, gap_minutes: int
) -> pd.DataFrame:
    result = df.copy()
    gaps = result["_timestamp"].diff().dt.total_seconds()
    new_session = gaps.isna() | gaps.gt(gap_minutes * 60)
    result["session_id"] = new_session.cumsum().astype(int)
    return result


def chronological_session_split(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sessions = (
        df.groupby("session_id", sort=False)["_timestamp"]
        .agg(start="min", end="max", rows="size")
        .sort_values("start")
    )

    if len(sessions) < 5:
        raise ValueError(f"Too few sessions for evaluation: {len(sessions)}")

    split_index = int(len(sessions) * TRAIN_FRACTION)
    split_index = min(max(split_index, 1), len(sessions) - 1)

    train_ids = set(sessions.index[:split_index])
    eval_ids = set(sessions.index[split_index:])

    train = df[df["session_id"].isin(train_ids)].copy()
    evaluation = df[df["session_id"].isin(eval_ids)].copy()

    if set(train["session_id"]) & set(evaluation["session_id"]):
        raise RuntimeError("Session leakage detected.")

    return train, evaluation


def encode_for_forest(
    train: pd.DataFrame, evaluation: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_frame = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    eval_frame = evaluation[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()

    for column in CATEGORICAL_FEATURES:
        train_frame[column] = train_frame[column].astype(str)
        eval_frame[column] = eval_frame[column].astype(str)

    train_encoded = pd.get_dummies(train_frame, columns=CATEGORICAL_FEATURES)
    eval_encoded = pd.get_dummies(eval_frame, columns=CATEGORICAL_FEATURES)
    eval_encoded = eval_encoded.reindex(
        columns=train_encoded.columns, fill_value=0
    )

    return (
        train_encoded.astype(float),
        eval_encoded.astype(float),
    )


def robust_scores(
    train: pd.DataFrame, evaluation: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, dict]:
    medians = {}
    scales = {}

    for feature in NUMERIC_FEATURES:
        values = train[feature].astype(float).to_numpy()
        median = float(np.median(values))
        mad = float(1.4826 * np.median(np.abs(values - median)))
        iqr = float(
            (np.quantile(values, 0.75) - np.quantile(values, 0.25)) / 1.349
        )
        std = float(np.std(values))
        scale = max(mad, iqr, std, 1e-6)

        medians[feature] = median
        scales[feature] = scale

    centers = np.array([medians[f] for f in NUMERIC_FEATURES])
    feature_scales = np.array([scales[f] for f in NUMERIC_FEATURES])

    def score(frame: pd.DataFrame) -> np.ndarray:
        values = frame[NUMERIC_FEATURES].astype(float).to_numpy()
        z = np.abs((values - centers) / feature_scales)
        return np.max(z, axis=1)

    return score(train), score(evaluation), {
        "features": NUMERIC_FEATURES,
        "medians": medians,
        "scales": scales,
        "method": "maximum absolute robust z-score",
    }


def threshold_comparison(
    train_scores: np.ndarray,
    eval_scores: np.ndarray,
    higher_is_anomalous: bool,
) -> dict:
    results = {}

    for rate in THRESHOLDS:
        if higher_is_anomalous:
            threshold = float(np.quantile(train_scores, 1 - rate))
            flags = eval_scores > threshold
        else:
            threshold = float(np.quantile(train_scores, rate))
            flags = eval_scores < threshold

        results[f"{rate:.0%}"] = {
            "training_quantile": float(1 - rate if higher_is_anomalous else rate),
            "threshold": threshold,
            "flagged_count": int(flags.sum()),
            "evaluation_count": int(len(flags)),
            "flagged_rate_pct": float(flags.mean() * 100),
            "flagged_positions": np.flatnonzero(flags).astype(int).tolist(),
        }

    return results


def compare_flag_overlap(
    forest_flags: np.ndarray,
    baseline_flags: np.ndarray,
) -> dict:
    forest_set = set(np.flatnonzero(forest_flags).tolist())
    baseline_set = set(np.flatnonzero(baseline_flags).tolist())
    union = forest_set | baseline_set
    intersection = forest_set & baseline_set

    return {
        "forest_flagged": len(forest_set),
        "baseline_flagged": len(baseline_set),
        "both_flagged": len(intersection),
        "forest_only": len(forest_set - baseline_set),
        "baseline_only": len(baseline_set - forest_set),
        "union_flagged": len(union),
        "jaccard_overlap_pct": (
            float(len(intersection) / len(union) * 100) if union else 100.0
        ),
        "shared_evaluation_positions": sorted(intersection),
    }


def summarize_sessions(
    evaluation: pd.DataFrame,
    forest_flags: np.ndarray,
    baseline_flags: np.ndarray,
) -> dict:
    working = evaluation.copy().reset_index(drop=True)
    working["forest_flag"] = forest_flags
    working["baseline_flag"] = baseline_flags

    forest_sessions = set(
        working.loc[working["forest_flag"], "session_id"].astype(int)
    )
    baseline_sessions = set(
        working.loc[working["baseline_flag"], "session_id"].astype(int)
    )

    return {
        "evaluation_sessions": int(working["session_id"].nunique()),
        "sessions_with_forest_flags": len(forest_sessions),
        "sessions_with_baseline_flags": len(baseline_sessions),
        "sessions_flagged_by_both": len(forest_sessions & baseline_sessions),
        "sessions_flagged_only_by_forest": len(
            forest_sessions - baseline_sessions
        ),
        "sessions_flagged_only_by_baseline": len(
            baseline_sessions - forest_sessions
        ),
        "flagged_session_ids": {
            "forest": sorted(forest_sessions),
            "baseline": sorted(baseline_sessions),
        },
    }


def run_gap_benchmark(
    base_df: pd.DataFrame,
    gap_minutes: int,
) -> dict:
    df = assign_sessions(base_df, gap_minutes)
    train, evaluation = chronological_session_split(df)

    train_encoded, eval_encoded = encode_for_forest(train, evaluation)

    forest = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    forest.fit(train_encoded)

    # Lower decision_function scores are more anomalous.
    forest_train_scores = forest.decision_function(train_encoded)
    forest_eval_scores = forest.decision_function(eval_encoded)

    baseline_train_scores, baseline_eval_scores, scaling = robust_scores(
        train, evaluation
    )

    forest_comparison = threshold_comparison(
        forest_train_scores, forest_eval_scores, higher_is_anomalous=False
    )
    baseline_comparison = threshold_comparison(
        baseline_train_scores, baseline_eval_scores, higher_is_anomalous=True
    )

    overlaps = {}
    session_summaries = {}

    for rate in THRESHOLDS:
        key = f"{rate:.0%}"
        forest_flags = np.zeros(len(evaluation), dtype=bool)
        baseline_flags = np.zeros(len(evaluation), dtype=bool)

        forest_positions = forest_comparison[key]["flagged_positions"]
        baseline_positions = baseline_comparison[key]["flagged_positions"]
        forest_flags[forest_positions] = True
        baseline_flags[baseline_positions] = True

        overlaps[key] = compare_flag_overlap(forest_flags, baseline_flags)
        session_summaries[key] = summarize_sessions(
            evaluation, forest_flags, baseline_flags
        )

    session_info = (
        df.groupby("session_id")["_timestamp"]
        .agg(start="min", end="max", rows="size")
        .sort_values("start")
    )
    split_index = int(len(session_info) * TRAIN_FRACTION)
    split_index = min(max(split_index, 1), len(session_info) - 1)

    return {
        "session_gap_minutes": gap_minutes,
        "split": {
            "total_sessions": int(len(session_info)),
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
            "split_index": split_index,
        },
        "detectors": {
            "isolation_forest": forest_comparison,
            "robust_statistical_baseline_v2": baseline_comparison,
        },
        "flag_overlap": overlaps,
        "session_overlap": session_summaries,
        "baseline_scaling": scaling,
    }


def main() -> None:
    started = time.perf_counter()

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    dataset_hash = sha256_file(DATASET_PATH)
    business, schema = load_business_data()
    featured = add_features(business)

    gap_results = {}
    for gap_minutes in SESSION_GAPS_MINUTES:
        print(f"Benchmarking session gap: {gap_minutes} minute(s)...")
        gap_results[str(gap_minutes)] = run_gap_benchmark(
            featured, gap_minutes
        )

    report = {
        "report_version": 3,
        "experiment": EXPERIMENT_NAME,
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "dataset_sha256": dataset_hash,
        "dataset_rows": int(len(business)),
        "schema": schema,
        "evaluation_method": (
            "Chronological session holdout, repeated for 1-, 5-, and "
            "15-minute inactivity session definitions. Detector thresholds "
            "are calibrated on training scores at 1%, 2%, and 5% tails."
        ),
        "thresholds": list(THRESHOLDS),
        "session_gaps_minutes": list(SESSION_GAPS_MINUTES),
        "labels_available": False,
        "accuracy_metrics_available": False,
        "interpretation": (
            "Exploratory detector comparison only. Anomaly rates and overlap "
            "do not establish precision, recall, F1, or real incident validity. "
            "Different session definitions change the chronological split, "
            "so compare the split coverage as well as the scores."
        ),
        "results_by_session_gap_minutes": gap_results,
        "production_models_modified": False,
        "existing_risk_report_modified": False,
        "total_runtime_seconds": time.perf_counter() - started,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    mlflow.set_tracking_uri(
        os.getenv("MLFLOW_TRACKING_URI")
        or f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}"
    )
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="business-detector-benchmark-v3") as run:
        mlflow.set_tags({
            "benchmark_version": "3",
            "dataset_sha256": dataset_hash,
            "production_model_modified": "false",
            "labels_available": "false",
        })
        mlflow.log_params({
            "session_gaps_minutes": ",".join(
                map(str, SESSION_GAPS_MINUTES)
            ),
            "thresholds": ",".join(f"{rate:.0%}" for rate in THRESHOLDS),
            "training_session_fraction": TRAIN_FRACTION,
            "isolation_forest_estimators": 300,
            "random_state": RANDOM_STATE,
        })

        metrics = {
            "dataset_rows": len(business),
            "total_runtime_seconds": report["total_runtime_seconds"],
        }

        for gap, result in gap_results.items():
            for rate in THRESHOLDS:
                key = f"{rate:.0%}"
                prefix = f"gap_{gap}m_{int(rate * 100)}pct"

                metrics[f"{prefix}_forest_anomaly_rate_pct"] = result[
                    "detectors"
                ]["isolation_forest"][key]["flagged_rate_pct"]
                metrics[f"{prefix}_baseline_anomaly_rate_pct"] = result[
                    "detectors"
                ]["robust_statistical_baseline_v2"][key]["flagged_rate_pct"]
                metrics[f"{prefix}_jaccard_overlap_pct"] = result[
                    "flag_overlap"
                ][key]["jaccard_overlap_pct"]

            metrics[f"gap_{gap}m_train_rows"] = result["split"]["training_rows"]
            metrics[f"gap_{gap}m_eval_rows"] = result["split"]["evaluation_rows"]
            metrics[f"gap_{gap}m_eval_active_days"] = result["split"][
                "evaluation_active_days"
            ]

        mlflow.log_metrics({
            key: float(value) for key, value in metrics.items()
        })
        mlflow.log_artifact(str(REPORT_PATH), artifact_path="reports")
        report["mlflow_run_id"] = run.info.run_id

    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nReport: {REPORT_PATH}")
    print(f"Dataset SHA-256: {dataset_hash}")
    print(f"MLflow run ID: {report['mlflow_run_id']}")
    print(f"Dataset rows: {len(business)}")

    for gap, result in gap_results.items():
        print(f"\nSession gap: {gap} minute(s)")
        split = result["split"]
        print(
            f"Train: {split['training_rows']} rows, "
            f"{split['training_active_days']} active days"
        )
        print(
            f"Evaluation: {split['evaluation_rows']} rows, "
            f"{split['evaluation_active_days']} active days"
        )

        for rate in THRESHOLDS:
            key = f"{rate:.0%}"
            forest = result["detectors"]["isolation_forest"][key]
            baseline = result["detectors"][
                "robust_statistical_baseline_v2"
            ][key]
            overlap = result["flag_overlap"][key]

            print(
                f"  {key}: forest={forest['flagged_count']} "
                f"({forest['flagged_rate_pct']:.2f}%), "
                f"baseline={baseline['flagged_count']} "
                f"({baseline['flagged_rate_pct']:.2f}%), "
                f"overlap={overlap['both_flagged']}, "
                f"Jaccard={overlap['jaccard_overlap_pct']:.1f}%"
            )

    print("\nProduction models and existing risk report were not modified.")


if __name__ == "__main__":
    main()