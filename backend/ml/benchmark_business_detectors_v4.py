from __future__ import annotations

import hashlib
import json
import time
from collections import deque
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path.cwd()

DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
REPORT_DIR = ROOT / "data" / "reports"
REPORT_PATH = REPORT_DIR / "business_detector_benchmark_v4.json"

MLFLOW_DB_PATH = (ROOT / "mlflow.db").resolve()
MLFLOW_TRACKING_URI = f"sqlite:///{MLFLOW_DB_PATH.as_posix()}"

EXPERIMENT_NAME = "KBR-Anomaly-Detection"

RANDOM_STATE = 42
N_ESTIMATORS = 300
TRAINING_SESSION_FRACTION = 0.80

SESSION_GAPS_MINUTES = [1, 5]
ALERT_BUDGETS = [0.01, 0.02, 0.05]

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


# ---------------------------------------------------------------------------
# General utilities
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        value = float(value)
        return value if np.isfinite(value) else None

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, float) and not np.isfinite(value):
        return None

    return value


def quantile_summary(scores: np.ndarray) -> dict[str, Any]:
    scores = np.asarray(scores, dtype=float)
    scores = scores[np.isfinite(scores)]

    if len(scores) == 0:
        return {"count": 0}

    quantiles = np.quantile(
        scores,
        [0.00, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 1.00],
    )

    return {
        "count": int(len(scores)),
        "unique_exact_scores": int(np.unique(scores).size),
        "unique_scores_rounded_8dp": int(
            np.unique(np.round(scores, 8)).size
        ),
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "min": float(quantiles[0]),
        "p01": float(quantiles[1]),
        "p05": float(quantiles[2]),
        "p10": float(quantiles[3]),
        "p25": float(quantiles[4]),
        "median": float(quantiles[5]),
        "p75": float(quantiles[6]),
        "p90": float(quantiles[7]),
        "p95": float(quantiles[8]),
        "p99": float(quantiles[9]),
        "max": float(quantiles[10]),
    }


def active_day_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0

    return int(frame["_timestamp"].dt.floor("D").nunique())


# ---------------------------------------------------------------------------
# Dataset loading and causal feature engineering
# ---------------------------------------------------------------------------

def load_dataset() -> tuple[pd.DataFrame, dict[str, Any]]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}\n"
            "Run this script from the KBR project root."
        )

    raw = pd.read_csv(DATASET_PATH)

    if raw.empty:
        raise ValueError("The input dataset is empty.")

    timestamp_column = next(
        (
            column
            for column in ["occurred_at", "created_at", "timestamp"]
            if column in raw.columns
        ),
        None,
    )

    if timestamp_column is None:
        raise ValueError(
            "No supported timestamp column found. "
            "Expected occurred_at, created_at, or timestamp."
        )

    raw["_timestamp"] = pd.to_datetime(
        raw[timestamp_column],
        errors="coerce",
        format="mixed",
        utc=True,
    )

    invalid_timestamps = int(raw["_timestamp"].isna().sum())
    raw = raw.dropna(subset=["_timestamp"]).copy()

    # Preserve the population-selection policy used in v3:
    # filter to business rows only if the dataset explicitly identifies
    # business and HTTP populations. Otherwise, use the complete dataset.
    population_column = next(
        (
            column
            for column in ["population", "activity_population", "event_type"]
            if column in raw.columns
        ),
        None,
    )

    population_filter_applied = False

    if population_column is not None:
        values = (
            raw[population_column]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        has_http = values.str.contains(
            "http|request",
            regex=True,
            na=False,
        ).any()

        has_business = values.str.contains(
            "business",
            regex=True,
            na=False,
        ).any()

        if has_http and has_business:
            raw = raw.loc[
                ~values.str.contains("http|request", regex=True, na=False)
            ].copy()
            population_filter_applied = True

    raw = raw.sort_values(
        "_timestamp",
        kind="stable",
    ).reset_index(drop=True)

    for column in CATEGORICAL_FEATURES:
        if column not in raw.columns:
            raw[column] = "__MISSING__"

        raw[column] = (
            raw[column]
            .astype("string")
            .fillna("__MISSING__")
            .astype(str)
        )

    metadata = {
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "dataset_sha256": sha256_file(DATASET_PATH),
        "original_rows": int(len(pd.read_csv(DATASET_PATH))),
        "valid_timestamp_rows": int(len(raw)),
        "invalid_timestamp_rows": invalid_timestamps,
        "timestamp_column": timestamp_column,
        "population_column": population_column,
        "population_filter_applied": population_filter_applied,
        "rows_used": int(len(raw)),
        "categorical_columns_present_or_created": CATEGORICAL_FEATURES,
    }

    return raw, metadata


def build_causal_features(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Construct features using only the current timestamp and preceding events.

    The current row is excluded from the rolling counts.
    """
    result = frame.copy()
    timestamps = result["_timestamp"]

    seconds_since_previous = (
        timestamps.diff().dt.total_seconds()
    )

    # First event has no previous event; use the maximum observed gap
    # as a conservative, finite fallback.
    positive_gaps = seconds_since_previous[
        seconds_since_previous > 0
    ]

    fallback_gap = (
        float(positive_gaps.median())
        if not positive_gaps.empty
        else 60.0
    )

    seconds_since_previous = seconds_since_previous.fillna(fallback_gap)
    seconds_since_previous = seconds_since_previous.clip(lower=0.001)

    result["gap_log_seconds"] = np.log1p(seconds_since_previous)

    previous_5m: deque[pd.Timestamp] = deque()
    previous_1h: deque[pd.Timestamp] = deque()

    count_5m: list[int] = []
    count_1h: list[int] = []

    for timestamp in timestamps:
        cutoff_5m = timestamp - pd.Timedelta(minutes=5)
        cutoff_1h = timestamp - pd.Timedelta(hours=1)

        while previous_5m and previous_5m[0] <= cutoff_5m:
            previous_5m.popleft()

        while previous_1h and previous_1h[0] <= cutoff_1h:
            previous_1h.popleft()

        # Counts are recorded before adding the current event.
        count_5m.append(len(previous_5m))
        count_1h.append(len(previous_1h))

        previous_5m.append(timestamp)
        previous_1h.append(timestamp)

    result["events_previous_5m"] = count_5m
    result["events_previous_1h"] = count_1h

    result[NUMERIC_FEATURES] = (
        result[NUMERIC_FEATURES]
        .replace([np.inf, -np.inf], np.nan)
    )

    return result


# ---------------------------------------------------------------------------
# Session grouping and shared chronological evaluation window
# ---------------------------------------------------------------------------

def assign_sessions(
    frame: pd.DataFrame,
    gap_minutes: int,
) -> pd.DataFrame:
    result = frame.copy()

    gaps = result["_timestamp"].diff().dt.total_seconds()

    starts_new_session = (
        gaps.isna()
        | (gaps > gap_minutes * 60)
    )

    result["_session_id"] = (
        starts_new_session.cumsum().astype(int) - 1
    )

    return result


def initial_split_cutoff(
    frame: pd.DataFrame,
    gap_minutes: int,
) -> dict[str, Any]:
    grouped = assign_sessions(frame, gap_minutes)

    session_table = (
        grouped.groupby("_session_id", sort=True)
        .agg(
            session_start=("_timestamp", "min"),
            session_end=("_timestamp", "max"),
            row_count=("_timestamp", "size"),
        )
        .sort_values("session_start")
        .reset_index()
    )

    session_count = len(session_table)

    if session_count < 5:
        raise ValueError(
            f"Only {session_count} sessions for {gap_minutes}-minute gap; "
            "not enough for an 80/20 chronological split."
        )

    split_index = int(
        np.floor(session_count * TRAINING_SESSION_FRACTION)
    )
    split_index = min(max(split_index, 1), session_count - 1)

    cutoff = session_table.loc[split_index, "session_start"]

    return {
        "gap_minutes": gap_minutes,
        "session_count": int(session_count),
        "split_index": int(split_index),
        "provisional_cutoff": cutoff,
        "provisional_training_sessions": int(split_index),
        "provisional_evaluation_sessions": int(
            session_count - split_index
        ),
    }


def shared_temporal_split(
    frame: pd.DataFrame,
) -> tuple[pd.Timestamp, dict[str, Any]]:
    provisional = [
        initial_split_cutoff(frame, gap)
        for gap in SESSION_GAPS_MINUTES
    ]

    # Use the latest provisional cutoff so every gap definition is
    # evaluated over the same chronological time horizon.
    common_cutoff = max(
        item["provisional_cutoff"]
        for item in provisional
    )

    metadata = {
        "method": (
            "Common timestamp cutoff based on the latest provisional "
            "80/20 chronological session split. Sessions crossing the "
            "cutoff are excluded from both train and evaluation."
        ),
        "common_evaluation_start": common_cutoff.isoformat(),
        "provisional_splits": [
            {
                **item,
                "provisional_cutoff": item[
                    "provisional_cutoff"
                ].isoformat(),
            }
            for item in provisional
        ],
    }

    return common_cutoff, metadata


def split_without_session_leakage(
    frame: pd.DataFrame,
    gap_minutes: int,
    cutoff: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    grouped = assign_sessions(frame, gap_minutes)

    session_table = (
        grouped.groupby("_session_id", sort=True)
        .agg(
            session_start=("_timestamp", "min"),
            session_end=("_timestamp", "max"),
            row_count=("_timestamp", "size"),
        )
    )

    train_session_ids = set(
        session_table.index[
            session_table["session_end"] < cutoff
        ]
    )

    eval_session_ids = set(
        session_table.index[
            session_table["session_start"] >= cutoff
        ]
    )

    crossing_session_ids = set(
        session_table.index[
            (session_table["session_start"] < cutoff)
            & (session_table["session_end"] >= cutoff)
        ]
    )

    train = grouped[
        grouped["_session_id"].isin(train_session_ids)
    ].copy()

    evaluation = grouped[
        grouped["_session_id"].isin(eval_session_ids)
    ].copy()

    metadata = {
        "session_gap_minutes": gap_minutes,
        "training_sessions": int(len(train_session_ids)),
        "evaluation_sessions": int(len(eval_session_ids)),
        "crossing_sessions_excluded": int(len(crossing_session_ids)),
        "training_rows": int(len(train)),
        "evaluation_rows": int(len(evaluation)),
        "training_active_days": active_day_count(train),
        "evaluation_active_days": active_day_count(evaluation),
        "training_start": (
            train["_timestamp"].min().isoformat()
            if not train.empty
            else None
        ),
        "training_end": (
            train["_timestamp"].max().isoformat()
            if not train.empty
            else None
        ),
        "evaluation_start": (
            evaluation["_timestamp"].min().isoformat()
            if not evaluation.empty
            else None
        ),
        "evaluation_end": (
            evaluation["_timestamp"].max().isoformat()
            if not evaluation.empty
            else None
        ),
        "common_cutoff": cutoff.isoformat(),
        "sessions_crossing_split": 0,
    }

    if train.empty or evaluation.empty:
        raise ValueError(
            f"Empty train/evaluation partition for {gap_minutes}-minute gap."
        )

    if train["_timestamp"].max() >= evaluation["_timestamp"].min():
        raise AssertionError(
            "Chronological split invariant violated."
        )

    if train_session_ids & eval_session_ids:
        raise AssertionError(
            "A session appears in both train and evaluation."
        )

    return train, evaluation, metadata


# ---------------------------------------------------------------------------
# Detector pipelines
# ---------------------------------------------------------------------------

def make_isolation_forest() -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
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
                    sparse_output=True,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    detector = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("detector", detector),
        ]
    )


def robust_scale(
    training: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    values = training[NUMERIC_FEATURES].to_numpy(dtype=float)

    medians = np.nanmedian(values, axis=0)
    medians = np.where(np.isfinite(medians), medians, 0.0)

    imputed = np.where(np.isfinite(values), values, medians)

    # Median absolute deviation, scaled to approximate standard deviation.
    mad = np.median(
        np.abs(imputed - medians),
        axis=0,
    )

    scales = 1.4826 * mad

    # If MAD is zero or too small, fall back to IQR / 1.349,
    # then standard deviation, then 1.0.
    q25 = np.quantile(imputed, 0.25, axis=0)
    q75 = np.quantile(imputed, 0.75, axis=0)
    iqr_scale = (q75 - q25) / 1.349
    std_scale = np.std(imputed, axis=0)

    for index in range(len(scales)):
        if not np.isfinite(scales[index]) or scales[index] < 1e-6:
            scales[index] = iqr_scale[index]

        if not np.isfinite(scales[index]) or scales[index] < 1e-6:
            scales[index] = std_scale[index]

        if not np.isfinite(scales[index]) or scales[index] < 1e-6:
            scales[index] = 1.0

    scaling_report = {
        "features": NUMERIC_FEATURES,
        "medians": {
            name: float(value)
            for name, value in zip(NUMERIC_FEATURES, medians)
        },
        "scales": {
            name: float(value)
            for name, value in zip(NUMERIC_FEATURES, scales)
        },
        "method": "MAD, then IQR, then standard deviation, then 1.0",
        "minimum_scale": float(np.min(scales)),
        "near_zero_scale_count": int(np.sum(scales < 1e-6)),
    }

    return medians, scales, scaling_report


def baseline_scores(
    training: pd.DataFrame,
    evaluation: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    medians, scales, scaling_report = robust_scale(training)

    train_values = training[NUMERIC_FEATURES].to_numpy(dtype=float)
    eval_values = evaluation[NUMERIC_FEATURES].to_numpy(dtype=float)

    train_values = np.where(
        np.isfinite(train_values),
        train_values,
        medians,
    )
    eval_values = np.where(
        np.isfinite(eval_values),
        eval_values,
        medians,
    )

    train_z = np.abs((train_values - medians) / scales)
    eval_z = np.abs((eval_values - medians) / scales)

    # Higher scores always mean more anomalous.
    train_scores = np.max(train_z, axis=1)
    eval_scores = np.max(eval_z, axis=1)

    return train_scores, eval_scores, scaling_report


# ---------------------------------------------------------------------------
# Threshold diagnostics and fixed alert budgets
# ---------------------------------------------------------------------------

def threshold_diagnostics(
    train_scores: np.ndarray,
    eval_scores: np.ndarray,
    tail_rate: float,
) -> dict[str, Any]:
    """
    Calibrate a high-score threshold using the training score tail.
    The actual evaluation alert rate may exceed the nominal tail when
    scores are tied or the evaluation distribution differs from training.
    """
    train_scores = np.asarray(train_scores, dtype=float)
    eval_scores = np.asarray(eval_scores, dtype=float)

    threshold = float(
        np.quantile(train_scores, 1.0 - tail_rate)
    )

    train_at_threshold = int(
        np.sum(train_scores >= threshold)
    )
    eval_at_threshold = int(
        np.sum(eval_scores >= threshold)
    )

    tied_train = int(np.sum(train_scores == threshold))
    tied_eval = int(np.sum(eval_scores == threshold))

    return {
        "nominal_training_tail_pct": tail_rate * 100,
        "threshold": threshold,
        "training_count": int(len(train_scores)),
        "training_flagged_count": train_at_threshold,
        "training_flagged_rate_pct": (
            100 * train_at_threshold / len(train_scores)
            if len(train_scores)
            else 0.0
        ),
        "training_scores_equal_to_threshold": tied_train,
        "evaluation_count": int(len(eval_scores)),
        "evaluation_flagged_count": eval_at_threshold,
        "evaluation_flagged_rate_pct": (
            100 * eval_at_threshold / len(eval_scores)
            if len(eval_scores)
            else 0.0
        ),
        "evaluation_scores_equal_to_threshold": tied_eval,
        "evaluation_threshold_tie_fraction_pct": (
            100 * tied_eval / len(eval_scores)
            if len(eval_scores)
            else 0.0
        ),
        "evaluation_threshold_exceedances_including_ties": eval_at_threshold,
    }


def top_k_alerts(
    evaluation: pd.DataFrame,
    scores: np.ndarray,
    budget: float,
) -> dict[str, Any]:
    """
    Select exactly floor(budget * N) alerts by rank.

    Stable row order breaks ties at the selection boundary. This is an
    alert-budget comparison, not an accuracy measurement.
    """
    scores = np.asarray(scores, dtype=float)
    count = len(scores)

    k = max(1, int(np.floor(count * budget))) if count else 0

    order = np.argsort(-scores, kind="stable")
    selected_positions = order[:k]

    selected_scores = scores[selected_positions]

    if k:
        boundary_score = float(selected_scores[-1])
        all_tied_at_boundary = int(
            np.sum(scores == boundary_score)
        )
        selected_at_boundary = int(
            np.sum(selected_scores == boundary_score)
        )
    else:
        boundary_score = None
        all_tied_at_boundary = 0
        selected_at_boundary = 0

    selected = evaluation.iloc[selected_positions]

    category_counts: dict[str, dict[str, int]] = {}

    for column in CATEGORICAL_FEATURES:
        if column in selected.columns:
            category_counts[column] = {
                str(key): int(value)
                for key, value in (
                    selected[column]
                    .astype(str)
                    .value_counts()
                    .head(10)
                    .items()
                )
            }

    return {
        "budget_pct": budget * 100,
        "selected_count": int(k),
        "evaluation_count": int(count),
        "selected_rate_pct": (
            100 * k / count if count else 0.0
        ),
        "minimum_selected_score": boundary_score,
        "rows_tied_at_selection_boundary": all_tied_at_boundary,
        "tied_rows_selected_at_boundary": selected_at_boundary,
        "tie_break": "Stable evaluation row order",
        "top_score_mean": (
            float(np.mean(selected_scores))
            if k
            else None
        ),
        "top_score_min": (
            float(np.min(selected_scores))
            if k
            else None
        ),
        "selected_timestamp_start": (
            selected["_timestamp"].min().isoformat()
            if k
            else None
        ),
        "selected_timestamp_end": (
            selected["_timestamp"].max().isoformat()
            if k
            else None
        ),
        "selected_category_counts_top_10": category_counts,
    }


def overlap_report(
    forest_scores: np.ndarray,
    baseline_scores_array: np.ndarray,
    evaluation: pd.DataFrame,
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for budget in ALERT_BUDGETS:
        forest = top_k_alerts(evaluation, forest_scores, budget)
        baseline = top_k_alerts(
            evaluation,
            baseline_scores_array,
            budget,
        )

        k_forest = forest["selected_count"]
        k_baseline = baseline["selected_count"]

        forest_positions = set(
            np.argsort(-forest_scores, kind="stable")[:k_forest]
        )
        baseline_positions = set(
            np.argsort(
                -baseline_scores_array,
                kind="stable",
            )[:k_baseline]
        )

        intersection = forest_positions & baseline_positions
        union = forest_positions | baseline_positions

        result[f"{int(budget * 100)}%"] = {
            "forest_selected": int(len(forest_positions)),
            "baseline_selected": int(len(baseline_positions)),
            "overlap_count": int(len(intersection)),
            "union_count": int(len(union)),
            "jaccard_pct": (
                100 * len(intersection) / len(union)
                if union
                else 0.0
            ),
            "forest_only_count": int(
                len(forest_positions - baseline_positions)
            ),
            "baseline_only_count": int(
                len(baseline_positions - forest_positions)
            ),
            "interpretation": (
                "Ranking agreement only; no labels are available."
            ),
        }

    return result


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def benchmark_gap(
    frame: pd.DataFrame,
    gap_minutes: int,
    cutoff: pd.Timestamp,
) -> dict[str, Any]:
    train, evaluation, split_report = split_without_session_leakage(
        frame,
        gap_minutes,
        cutoff,
    )

    print(
        f"\n--- {gap_minutes}-minute sessions ---\n"
        f"Training: {len(train)} rows, "
        f"{split_report['training_sessions']} sessions, "
        f"{split_report['training_active_days']} active days\n"
        f"Evaluation: {len(evaluation)} rows, "
        f"{split_report['evaluation_sessions']} sessions, "
        f"{split_report['evaluation_active_days']} active days"
    )

    if len(train) < 50 or len(evaluation) < 20:
        raise ValueError(
            f"Insufficient rows for {gap_minutes}-minute split: "
            f"train={len(train)}, evaluation={len(evaluation)}."
        )

    x_train = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    x_eval = evaluation[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    start = time.perf_counter()

    forest = make_isolation_forest()
    forest.fit(x_train)

    forest_training_runtime = time.perf_counter() - start

    # sklearn decision_function is higher for more normal observations.
    # Negating it makes higher values consistently mean more anomalous.
    forest_train_scores = -forest.decision_function(x_train)
    forest_eval_scores = -forest.decision_function(x_eval)

    baseline_train_scores, baseline_eval_scores, scaling_report = (
        baseline_scores(train, evaluation)
    )

    detector_scores = {
        "isolation_forest": {
            "training": forest_train_scores,
            "evaluation": forest_eval_scores,
        },
        "robust_statistical_baseline_v4": {
            "training": baseline_train_scores,
            "evaluation": baseline_eval_scores,
        },
    }

    detector_reports: dict[str, Any] = {}

    for detector_name, scores in detector_scores.items():
        train_scores = scores["training"]
        eval_scores = scores["evaluation"]

        threshold_report = {
            f"{int(rate * 100)}%": threshold_diagnostics(
                train_scores,
                eval_scores,
                rate,
            )
            for rate in ALERT_BUDGETS
        }

        detector_reports[detector_name] = {
            "training_score_distribution": quantile_summary(
                train_scores
            ),
            "evaluation_score_distribution": quantile_summary(
                eval_scores
            ),
            "threshold_diagnostics": threshold_report,
            "fixed_alert_budgets": {
                f"{int(rate * 100)}%": top_k_alerts(
                    evaluation,
                    eval_scores,
                    rate,
                )
                for rate in ALERT_BUDGETS
            },
        }

    report = {
        "session_gap_minutes": gap_minutes,
        "split": split_report,
        "detectors": detector_reports,
        "ranking_agreement": overlap_report(
            forest_eval_scores,
            baseline_eval_scores,
            evaluation,
        ),
        "baseline_scaling": scaling_report,
        "isolation_forest_training_runtime_seconds": (
            forest_training_runtime
        ),
        "features": {
            "numeric": NUMERIC_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
            "rolling_counts_exclude_current_event": True,
        },
        "labels_available": False,
        "accuracy_metrics_available": False,
        "production_models_modified": False,
        "existing_risk_report_modified": False,
    }

    return json_safe(report)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    start_time = time.perf_counter()

    print("=" * 72)
    print("KBR ANOMALY DETECTOR BENCHMARK V4")
    print("=" * 72)

    raw, dataset_metadata = load_dataset()
    features = build_causal_features(raw)

    print(f"Dataset rows used: {len(features)}")
    print(f"Dataset SHA-256: {dataset_metadata['dataset_sha256']}")

    common_cutoff, cutoff_report = shared_temporal_split(features)

    print(f"Shared evaluation cutoff: {common_cutoff.isoformat()}")

    results: dict[str, Any] = {}

    for gap_minutes in SESSION_GAPS_MINUTES:
        results[str(gap_minutes)] = benchmark_gap(
            features,
            gap_minutes,
            common_cutoff,
        )

    runtime = time.perf_counter() - start_time

    report = {
        "report_version": 4,
        "experiment": EXPERIMENT_NAME,
        "dataset": dataset_metadata,
        "evaluation_method": (
            "Shared chronological evaluation window for 1- and 5-minute "
            "session definitions. Sessions crossing the common cutoff are "
            "excluded. Threshold diagnostics use training score quantiles; "
            "fixed alert budgets compare rankings at equal alert counts."
        ),
        "common_cutoff": cutoff_report,
        "session_gaps_minutes": SESSION_GAPS_MINUTES,
        "alert_budgets": ALERT_BUDGETS,
        "labels_available": False,
        "accuracy_metrics_available": False,
        "interpretation": (
            "Exploratory unsupervised detector comparison only. "
            "No labels are available, so flagged rows and ranking overlap "
            "do not establish precision, recall, F1, or real incident "
            "validity. A shared chronological window improves comparability "
            "but does not eliminate temporal distribution shift."
        ),
        "results_by_session_gap_minutes": results,
        "production_models_modified": False,
        "existing_risk_report_modified": False,
        "total_runtime_seconds": runtime,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Log to a new run; no model artifacts or production paths are changed.
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(
        run_name="business-detector-benchmark-v4-shared-window"
    ) as run:
        report["mlflow_run_id"] = run.info.run_id

        mlflow.log_param("benchmark_version", 4)
        mlflow.log_param(
            "dataset_sha256",
            dataset_metadata["dataset_sha256"],
        )
        mlflow.log_param(
            "dataset_rows",
            dataset_metadata["rows_used"],
        )
        mlflow.log_param(
            "session_gaps_minutes",
            ",".join(map(str, SESSION_GAPS_MINUTES)),
        )
        mlflow.log_param(
            "common_evaluation_start",
            common_cutoff.isoformat(),
        )
        mlflow.log_param("n_estimators", N_ESTIMATORS)
        mlflow.log_param("random_state", RANDOM_STATE)
        mlflow.log_param(
            "training_session_fraction",
            TRAINING_SESSION_FRACTION,
        )
        mlflow.log_param("labels_available", False)

        mlflow.log_metric("dataset_rows", len(features))
        mlflow.log_metric("runtime_seconds", runtime)

        for gap, gap_report in results.items():
            split = gap_report["split"]
            prefix = f"gap_{gap}m"

            mlflow.log_metric(
                f"{prefix}_training_rows",
                split["training_rows"],
            )
            mlflow.log_metric(
                f"{prefix}_evaluation_rows",
                split["evaluation_rows"],
            )
            mlflow.log_metric(
                f"{prefix}_evaluation_active_days",
                split["evaluation_active_days"],
            )

            for detector_name, detector_report in (
                gap_report["detectors"].items()
            ):
                detector_prefix = f"{prefix}_{detector_name}"

                mlflow.log_metric(
                    f"{detector_prefix}_eval_unique_scores",
                    detector_report[
                        "evaluation_score_distribution"
                    ]["unique_exact_scores"],
                )

                mlflow.log_metric(
                    f"{detector_prefix}_eval_score_p95",
                    detector_report[
                        "evaluation_score_distribution"
                    ]["p95"],
                )

                for budget_key, budget_report in (
                    detector_report["fixed_alert_budgets"].items()
                ):
                    budget_tag = budget_key.replace("%", "pct")

                    mlflow.log_metric(
                        f"{detector_prefix}_top_{budget_tag}_count",
                        budget_report["selected_count"],
                    )

            for budget_key, agreement in (
                gap_report["ranking_agreement"].items()
            ):
                budget_tag = budget_key.replace("%", "pct")

                mlflow.log_metric(
                    f"{prefix}_jaccard_{budget_tag}",
                    agreement["jaccard_pct"],
                )

        REPORT_PATH.write_text(
            json.dumps(
                json_safe(report),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        mlflow.log_artifact(str(REPORT_PATH))

    print("\n" + "=" * 72)
    print("BENCHMARK V4 COMPLETED")
    print("=" * 72)

    for gap, gap_report in results.items():
        print(f"\nSession gap: {gap} minute(s)")
        split = gap_report["split"]

        print(
            f"Shared evaluation rows: {split['evaluation_rows']} "
            f"across {split['evaluation_active_days']} active days"
        )

        for detector_name, detector_report in (
            gap_report["detectors"].items()
        ):
            distribution = detector_report[
                "evaluation_score_distribution"
            ]

            print(
                f"\n{detector_name}\n"
                f"  Unique evaluation scores: "
                f"{distribution['unique_exact_scores']}\n"
                f"  Evaluation p95: {distribution['p95']:.6f}"
            )

            for budget_key, budget_report in (
                detector_report["fixed_alert_budgets"].items()
            ):
                print(
                    f"  Top {budget_key}: "
                    f"{budget_report['selected_count']} rows; "
                    f"boundary ties="
                    f"{budget_report['rows_tied_at_selection_boundary']}"
                )

        for budget_key, agreement in (
            gap_report["ranking_agreement"].items()
        ):
            print(
                f"  Ranking overlap at {budget_key}: "
                f"{agreement['overlap_count']} rows, "
                f"Jaccard={agreement['jaccard_pct']:.2f}%"
            )

    print(f"\nReport: {REPORT_PATH}")
    print(f"MLflow run ID: {report['mlflow_run_id']}")
    print("Production models modified: False")
    print("Existing risk report modified: False")


if __name__ == "__main__":
    main()