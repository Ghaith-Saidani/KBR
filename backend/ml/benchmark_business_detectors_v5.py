from __future__ import annotations
import os

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


# ============================================================================
# CONFIGURATION
# ============================================================================

ROOT = Path.cwd()

DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
REPORT_DIR = ROOT / "data" / "reports"
REPORT_PATH = REPORT_DIR / "business_detector_benchmark_v5.json"

MLFLOW_DB_PATH = (ROOT / "mlflow.db").resolve()
MLFLOW_TRACKING_URI = (
    os.getenv("MLFLOW_TRACKING_URI")
    or f"sqlite:///{MLFLOW_DB_PATH.as_posix()}"
)
EXPERIMENT_NAME = "KBR-Anomaly-Detection"

RANDOM_STATE = 42
N_ESTIMATORS = 300
TRAINING_SESSION_FRACTION = 0.80

SESSION_GAPS_MINUTES = [1, 5]
ALERT_BUDGETS = [0.01, 0.02, 0.05]

TIMESTAMP_COLUMN_CANDIDATES = [
    "occurred_at",
    "created_at",
    "timestamp",
]

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

# The dataset's HTTP records use this resource_type.
HTTP_RESOURCE_TYPE = "http_request"


# ============================================================================
# UTILITIES
# ============================================================================

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
        number = float(value)
        return number if np.isfinite(number) else None

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, float) and not np.isfinite(value):
        return None

    return value


def active_day_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0

    return int(frame["_timestamp"].dt.floor("D").nunique())


def score_distribution(scores: np.ndarray) -> dict[str, Any]:
    scores = np.asarray(scores, dtype=float)
    scores = scores[np.isfinite(scores)]

    if len(scores) == 0:
        return {"count": 0, "unique_exact_scores": 0}

    q = np.quantile(
        scores,
        [
            0.00, 0.01, 0.05, 0.10, 0.25,
            0.50, 0.75, 0.90, 0.95, 0.99, 1.00,
        ],
    )

    return {
        "count": int(len(scores)),
        "unique_exact_scores": int(np.unique(scores).size),
        "unique_scores_rounded_8dp": int(
            np.unique(np.round(scores, 8)).size
        ),
        "zero_score_count": int(np.sum(np.isclose(scores, 0.0))),
        "zero_score_pct": float(
            100 * np.sum(np.isclose(scores, 0.0)) / len(scores)
        ),
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "min": float(q[0]),
        "p01": float(q[1]),
        "p05": float(q[2]),
        "p10": float(q[3]),
        "p25": float(q[4]),
        "median": float(q[5]),
        "p75": float(q[6]),
        "p90": float(q[7]),
        "p95": float(q[8]),
        "p99": float(q[9]),
        "max": float(q[10]),
    }


# ============================================================================
# DATA LOADING: BUSINESS EVENTS ONLY
# ============================================================================

def load_business_dataset() -> tuple[pd.DataFrame, dict[str, Any]]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}\n"
            "Run this script from the KBR project root."
        )

    raw = pd.read_csv(DATASET_PATH)
    original_rows = len(raw)

    if raw.empty:
        raise ValueError("The input dataset is empty.")

    timestamp_column = next(
        (
            column
            for column in TIMESTAMP_COLUMN_CANDIDATES
            if column in raw.columns
        ),
        None,
    )

    if timestamp_column is None:
        raise ValueError(
            "No timestamp column found. Expected one of: "
            + ", ".join(TIMESTAMP_COLUMN_CANDIDATES)
        )

    if "resource_type" not in raw.columns:
        raise ValueError(
            "Cannot isolate business events: resource_type is missing."
        )

    raw["_timestamp"] = pd.to_datetime(
        raw[timestamp_column],
        errors="coerce",
        format="mixed",
        utc=True,
    )

    invalid_timestamp_rows = int(raw["_timestamp"].isna().sum())
    raw = raw.dropna(subset=["_timestamp"]).copy()


    resource_types = (
        raw["resource_type"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    # Explicitly treat missing resource types as non-HTTP.
    # This retains all valid-timestamp rows except HTTP requests.
    http_mask = resource_types.eq(HTTP_RESOURCE_TYPE).fillna(False)
    http_rows = int(http_mask.sum())

    business = raw.loc[~http_mask].copy()


    if business.empty:
        raise ValueError(
            "No business events remain after excluding HTTP records."
        )

    if len(business) < 100:
        raise ValueError(
            f"Only {len(business)} business rows remain; "
            "insufficient data for this benchmark."
        )

    business = business.sort_values(
        "_timestamp",
        kind="stable",
    ).reset_index(drop=True)

    # Fill missing categorical values consistently.
    for column in CATEGORICAL_FEATURES:
        if column not in business.columns:
            business[column] = "__MISSING__"

        business[column] = (
            business[column]
            .astype("string")
            .fillna("__MISSING__")
            .astype(str)
        )

    metadata = {
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "dataset_sha256": sha256_file(DATASET_PATH),
        "original_rows": int(original_rows),
        "invalid_timestamp_rows": invalid_timestamp_rows,
        "timestamp_column": timestamp_column,
        "rows_with_valid_timestamps": int(len(raw)),
        "http_rows_excluded": http_rows,
        "business_rows_used": int(len(business)),
        "business_resource_types": {
            str(key): int(value)
            for key, value in (
                business["resource_type"].value_counts().items()
            )
        },
        "business_start": business["_timestamp"].min().isoformat(),
        "business_end": business["_timestamp"].max().isoformat(),
        "population_policy": (
            "Exclude rows where resource_type == 'http_request'; "
            "benchmark remaining business events only."
        ),
    }

    return business, metadata


# ============================================================================
# CAUSAL FEATURE ENGINEERING
# ============================================================================

def build_causal_features(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Features at row t use only the current timestamp and preceding events.

    Rolling counts are measured before adding the current event.
    """
    result = frame.copy()
    timestamps = result["_timestamp"]

    gap_seconds = timestamps.diff().dt.total_seconds()
    positive_gaps = gap_seconds[gap_seconds > 0]

    fallback_gap = (
        float(positive_gaps.median())
        if not positive_gaps.empty
        else 60.0
    )

    gap_seconds = gap_seconds.fillna(fallback_gap).clip(lower=0.001)
    result["gap_log_seconds"] = np.log1p(gap_seconds)

    previous_5m: deque[pd.Timestamp] = deque()
    previous_1h: deque[pd.Timestamp] = deque()

    count_5m: list[int] = []
    count_1h: list[int] = []

    for timestamp in timestamps:
        cutoff_5m = timestamp - pd.Timedelta(5, unit="min")
        cutoff_1h = timestamp - pd.Timedelta(1, unit="h")

        while previous_5m and previous_5m[0] <= cutoff_5m:
            previous_5m.popleft()

        while previous_1h and previous_1h[0] <= cutoff_1h:
            previous_1h.popleft()

        count_5m.append(len(previous_5m))
        count_1h.append(len(previous_1h))

        previous_5m.append(timestamp)
        previous_1h.append(timestamp)

    result["events_previous_5m"] = count_5m
    result["events_previous_1h"] = count_1h

    result[NUMERIC_FEATURES] = result[NUMERIC_FEATURES].replace(
        [np.inf, -np.inf],
        np.nan,
    )

    return result


def validate_features(frame: pd.DataFrame) -> dict[str, Any]:
    report: dict[str, Any] = {
        "row_count": int(len(frame)),
        "required_columns_present": all(
            column in frame.columns
            for column in NUMERIC_FEATURES + CATEGORICAL_FEATURES
        ),
        "numeric_features": {},
        "categorical_features": {},
        "causal_rolling_counts_exclude_current_event": True,
    }

    for column in NUMERIC_FEATURES:
        values = pd.to_numeric(frame[column], errors="coerce")

        report["numeric_features"][column] = {
            "missing_count": int(values.isna().sum()),
            "infinite_count": int(
                np.isinf(values.to_numpy(dtype=float, na_value=np.nan)).sum()
            ),
            "minimum": (
                float(values.min()) if values.notna().any() else None
            ),
            "maximum": (
                float(values.max()) if values.notna().any() else None
            ),
            "unique_values": int(values.nunique(dropna=True)),
        }

    for column in CATEGORICAL_FEATURES:
        report["categorical_features"][column] = {
            "missing_count": int(frame[column].isna().sum()),
            "unique_values": int(frame[column].nunique(dropna=True)),
        }

    if not report["required_columns_present"]:
        raise ValueError("Required feature columns are missing.")

    for column in NUMERIC_FEATURES:
        if frame[column].notna().sum() == 0:
            raise ValueError(f"Feature {column} contains no valid values.")

    return json_safe(report)


# ============================================================================
# SESSION GROUPING AND COMMON CHRONOLOGICAL CUTOFF
# ============================================================================

def assign_sessions(
    frame: pd.DataFrame,
    gap_minutes: int,
) -> pd.DataFrame:
    result = frame.copy()
    gaps = result["_timestamp"].diff().dt.total_seconds()

    new_session = gaps.isna() | (gaps > gap_minutes * 60)

    result["_session_id"] = new_session.cumsum().astype(int) - 1
    return result


def provisional_cutoff(
    frame: pd.DataFrame,
    gap_minutes: int,
) -> dict[str, Any]:
    grouped = assign_sessions(frame, gap_minutes)

    sessions = (
        grouped.groupby("_session_id", sort=True)
        .agg(
            session_start=("_timestamp", "min"),
            session_end=("_timestamp", "max"),
            rows=("_timestamp", "size"),
        )
        .sort_values("session_start")
        .reset_index()
    )

    count = len(sessions)

    if count < 5:
        raise ValueError(
            f"Only {count} sessions for {gap_minutes}-minute grouping."
        )

    split_index = int(np.floor(count * TRAINING_SESSION_FRACTION))
    split_index = min(max(split_index, 1), count - 1)

    return {
        "gap_minutes": gap_minutes,
        "session_count": int(count),
        "split_index": int(split_index),
        "cutoff": sessions.loc[split_index, "session_start"],
    }


def get_common_cutoff(
    frame: pd.DataFrame,
) -> tuple[pd.Timestamp, dict[str, Any]]:
    provisional = [
        provisional_cutoff(frame, gap)
        for gap in SESSION_GAPS_MINUTES
    ]

    # Same timestamp cutoff for both session definitions.
    cutoff = max(item["cutoff"] for item in provisional)

    metadata = {
        "method": (
            "Use the latest provisional chronological 80/20 session cutoff "
            "so both session definitions share an evaluation start."
        ),
        "common_cutoff": cutoff.isoformat(),
        "provisional_splits": [
            {
                "gap_minutes": item["gap_minutes"],
                "session_count": item["session_count"],
                "split_index": item["split_index"],
                "cutoff": item["cutoff"].isoformat(),
            }
            for item in provisional
        ],
    }

    return cutoff, metadata


def split_sessions(
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
        )
    )

    train_ids = set(
        session_table.index[session_table["session_end"] < cutoff]
    )
    eval_ids = set(
        session_table.index[session_table["session_start"] >= cutoff]
    )
    crossing_ids = set(
        session_table.index[
            (session_table["session_start"] < cutoff)
            & (session_table["session_end"] >= cutoff)
        ]
    )

    train = grouped[grouped["_session_id"].isin(train_ids)].copy()
    evaluation = grouped[grouped["_session_id"].isin(eval_ids)].copy()

    if train.empty or evaluation.empty:
        raise ValueError(
            f"Empty partition for session gap {gap_minutes} minutes."
        )

    # Leakage checks.
    if train_ids & eval_ids:
        raise AssertionError("Session leakage detected.")

    if train["_timestamp"].max() >= evaluation["_timestamp"].min():
        raise AssertionError("Chronological split invariant failed.")

    metadata = {
        "session_gap_minutes": gap_minutes,
        "training_sessions": int(len(train_ids)),
        "evaluation_sessions": int(len(eval_ids)),
        "crossing_sessions_excluded": int(len(crossing_ids)),
        "training_rows": int(len(train)),
        "evaluation_rows": int(len(evaluation)),
        "training_active_days": active_day_count(train),
        "evaluation_active_days": active_day_count(evaluation),
        "training_start": train["_timestamp"].min().isoformat(),
        "training_end": train["_timestamp"].max().isoformat(),
        "evaluation_start": evaluation["_timestamp"].min().isoformat(),
        "evaluation_end": evaluation["_timestamp"].max().isoformat(),
        "common_cutoff": cutoff.isoformat(),
        "sessions_crossing_split": 0,
        "chronological_order_valid": True,
        "session_leakage_detected": False,
    }

    return train, evaluation, metadata


# ============================================================================
# DETECTOR 1: ISOLATION FOREST
# ============================================================================

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


# ============================================================================
# DETECTOR 2: DIRECTIONAL ROBUST STATISTICAL BASELINE
# ============================================================================

def fit_directional_baseline(
    training: pd.DataFrame,
) -> tuple[dict[str, float], dict[str, float], dict[str, Any]]:
    """
    The score only increases for:
      - shorter-than-usual inter-event gaps;
      - higher-than-usual previous 5-minute event counts;
      - higher-than-usual previous 1-hour event counts.

    Long gaps and low event counts do not increase the anomaly score.
    """
    medians: dict[str, float] = {}
    scales: dict[str, float] = {}
    feature_diagnostics: dict[str, Any] = {}

    for column in NUMERIC_FEATURES:
        values = pd.to_numeric(
            training[column],
            errors="coerce",
        ).to_numpy(dtype=float)

        valid = values[np.isfinite(values)]

        if len(valid) == 0:
            raise ValueError(
                f"Cannot fit directional baseline: {column} is empty."
            )

        median = float(np.median(valid))
        mad = float(np.median(np.abs(valid - median)))
        scale = 1.4826 * mad

        if not np.isfinite(scale) or scale < 1e-6:
            q25, q75 = np.quantile(valid, [0.25, 0.75])
            scale = float((q75 - q25) / 1.349)

        if not np.isfinite(scale) or scale < 1e-6:
            scale = float(np.std(valid))

        if not np.isfinite(scale) or scale < 1e-6:
            scale = 1.0

        medians[column] = median
        scales[column] = scale

        feature_diagnostics[column] = {
            "median": median,
            "scale": scale,
            "mad": mad,
            "training_min": float(np.min(valid)),
            "training_max": float(np.max(valid)),
            "scale_fallback_used": bool(mad * 1.4826 < 1e-6),
        }

    report = {
        "method": (
            "One-sided robust z-scores: short gaps and high rolling counts "
            "increase risk; long gaps and low counts do not."
        ),
        "medians": medians,
        "scales": scales,
        "features": feature_diagnostics,
        "near_zero_scale_count": int(
            sum(scale < 1e-6 for scale in scales.values())
        ),
    }

    return medians, scales, json_safe(report)


def score_directional_baseline(
    frame: pd.DataFrame,
    medians: dict[str, float],
    scales: dict[str, float],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    gap = pd.to_numeric(
        frame["gap_log_seconds"],
        errors="coerce",
    ).to_numpy(dtype=float)

    count_5m = pd.to_numeric(
        frame["events_previous_5m"],
        errors="coerce",
    ).to_numpy(dtype=float)

    count_1h = pd.to_numeric(
        frame["events_previous_1h"],
        errors="coerce",
    ).to_numpy(dtype=float)

    # A short gap is suspicious; a long gap is not.
    short_gap_score = np.maximum(
        0.0,
        (medians["gap_log_seconds"] - gap)
        / scales["gap_log_seconds"],
    )

    # High activity counts are suspicious; low counts are not.
    high_5m_score = np.maximum(
        0.0,
        (count_5m - medians["events_previous_5m"])
        / scales["events_previous_5m"],
    )

    high_1h_score = np.maximum(
        0.0,
        (count_1h - medians["events_previous_1h"])
        / scales["events_previous_1h"],
    )

    components = {
        "short_gap_score": short_gap_score,
        "high_5m_activity_score": high_5m_score,
        "high_1h_activity_score": high_1h_score,
    }

    score = np.maximum.reduce(
        [
            short_gap_score,
            high_5m_score,
            high_1h_score,
        ]
    )

    score = np.where(np.isfinite(score), score, 0.0)

    return score, components


# ============================================================================
# THRESHOLDS, ALERT BUDGETS, AND OVERLAP
# ============================================================================

def threshold_report(
    train_scores: np.ndarray,
    eval_scores: np.ndarray,
    nominal_tail: float,
) -> dict[str, Any]:
    threshold = float(np.quantile(train_scores, 1.0 - nominal_tail))

    train_flagged = train_scores >= threshold
    eval_flagged = eval_scores >= threshold

    return {
        "nominal_training_tail_pct": nominal_tail * 100,
        "threshold": threshold,
        "training_count": int(len(train_scores)),
        "training_flagged_count": int(train_flagged.sum()),
        "training_flagged_rate_pct": float(
            100 * train_flagged.mean()
        ),
        "training_scores_equal_to_threshold": int(
            np.sum(train_scores == threshold)
        ),
        "evaluation_count": int(len(eval_scores)),
        "evaluation_flagged_count": int(eval_flagged.sum()),
        "evaluation_flagged_rate_pct": float(
            100 * eval_flagged.mean()
        ),
        "evaluation_scores_equal_to_threshold": int(
            np.sum(eval_scores == threshold)
        ),
        "evaluation_scores_below_threshold": int(
            np.sum(eval_scores < threshold)
        ),
        "interpretation": (
            "The nominal tail is calibrated on training scores. "
            "The held-out flag rate may differ due to distribution shift."
        ),
    }


def select_top_k(
    frame: pd.DataFrame,
    scores: np.ndarray,
    budget: float,
) -> tuple[dict[str, Any], set[int]]:
    """
    Select a fixed number of rows by rank. If scores tie at the boundary,
    use stable row order and report the tie explicitly.
    """
    scores = np.asarray(scores, dtype=float)
    count = len(scores)
    k = min(count, max(1, int(np.floor(count * budget)))) if count else 0

    order = np.argsort(-scores, kind="stable")
    positions = order[:k]
    selected_scores = scores[positions]
    selected = frame.iloc[positions]

    if k:
        boundary_score = float(selected_scores[-1])
        tied_at_boundary = int(np.sum(scores == boundary_score))
        selected_boundary_ties = int(
            np.sum(selected_scores == boundary_score)
        )
    else:
        boundary_score = None
        tied_at_boundary = 0
        selected_boundary_ties = 0

    category_counts = {}

    for column in CATEGORICAL_FEATURES:
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

    alerts = []

    for position in positions:
        row = frame.iloc[int(position)]

        alerts.append(
            {
                "timestamp": row["_timestamp"].isoformat(),
                "action": str(row.get("action", "__MISSING__")),
                "method": str(row.get("method", "__MISSING__")),
                "resource_type": str(
                    row.get("resource_type", "__MISSING__")
                ),
                "score": float(scores[position]),
            }
        )

    result = {
        "budget_pct": budget * 100,
        "selected_count": int(k),
        "evaluation_count": int(count),
        "selected_rate_pct": float(100 * k / count) if count else 0.0,
        "minimum_selected_score": boundary_score,
        "rows_tied_at_selection_boundary": tied_at_boundary,
        "tied_rows_selected_at_boundary": selected_boundary_ties,
        "tie_break": "Stable evaluation row order",
        "top_score_mean": (
            float(np.mean(selected_scores)) if k else None
        ),
        "top_score_min": (
            float(np.min(selected_scores)) if k else None
        ),
        "selected_timestamp_start": (
            selected["_timestamp"].min().isoformat() if k else None
        ),
        "selected_timestamp_end": (
            selected["_timestamp"].max().isoformat() if k else None
        ),
        "selected_category_counts_top_10": category_counts,
        "selected_alerts": alerts,
    }

    return json_safe(result), set(map(int, positions))


def compare_rankings(
    frame: pd.DataFrame,
    forest_scores: np.ndarray,
    baseline_scores: np.ndarray,
) -> dict[str, Any]:
    result = {}

    for budget in ALERT_BUDGETS:
        forest_report, forest_positions = select_top_k(
            frame,
            forest_scores,
            budget,
        )
        baseline_report, baseline_positions = select_top_k(
            frame,
            baseline_scores,
            budget,
        )

        intersection = forest_positions & baseline_positions
        union = forest_positions | baseline_positions

        key = f"{int(budget * 100)}%"

        result[key] = {
            "forest_selected": int(len(forest_positions)),
            "baseline_selected": int(len(baseline_positions)),
            "overlap_count": int(len(intersection)),
            "union_count": int(len(union)),
            "jaccard_pct": (
                float(100 * len(intersection) / len(union))
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
                "Ranking agreement only; this is not an accuracy metric."
            ),
        }

    return result


# ============================================================================
# DRIFT DIAGNOSTICS
# ============================================================================

def numeric_psi(
    train: pd.Series,
    evaluation: pd.Series,
    bins: int = 10,
) -> dict[str, Any]:
    train_values = pd.to_numeric(train, errors="coerce").dropna().to_numpy()
    eval_values = pd.to_numeric(
        evaluation,
        errors="coerce",
    ).dropna().to_numpy()

    if len(train_values) < 10 or len(eval_values) < 10:
        return {
            "psi": None,
            "status": "Insufficient non-null values",
        }

    quantile_edges = np.quantile(
        train_values,
        np.linspace(0, 1, bins + 1),
    )

    edges = np.unique(quantile_edges)

    if len(edges) < 3:
        return {
            "psi": None,
            "status": "Insufficient unique training quantile edges",
        }

    edges[0] = -np.inf
    edges[-1] = np.inf

    train_counts, _ = np.histogram(train_values, bins=edges)
    eval_counts, _ = np.histogram(eval_values, bins=edges)

    epsilon = 1e-6

    train_pct = train_counts / max(train_counts.sum(), 1)
    eval_pct = eval_counts / max(eval_counts.sum(), 1)

    train_pct = np.clip(train_pct, epsilon, None)
    eval_pct = np.clip(eval_pct, epsilon, None)

    psi = float(
        np.sum(
            (eval_pct - train_pct)
            * np.log(eval_pct / train_pct)
        )
    )

    return {
        "psi": psi,
        "bins": int(len(edges) - 1),
        "training_count": int(len(train_values)),
        "evaluation_count": int(len(eval_values)),
        "interpretation": (
            "Descriptive drift indicator only; it does not measure "
            "detector accuracy."
        ),
    }


def feature_drift_report(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
) -> dict[str, Any]:
    numeric = {
        column: numeric_psi(train[column], evaluation[column])
        for column in NUMERIC_FEATURES
    }

    categorical = {}

    for column in CATEGORICAL_FEATURES:
        train_values = set(train[column].astype(str))
        eval_values = set(evaluation[column].astype(str))
        unseen_mask = ~evaluation[column].astype(str).isin(train_values)

        categorical[column] = {
            "training_unique_values": int(len(train_values)),
            "evaluation_unique_values": int(len(eval_values)),
            "unseen_evaluation_values": sorted(
                eval_values - train_values
            ),
            "unseen_evaluation_rows": int(unseen_mask.sum()),
            "unseen_evaluation_row_pct": float(
                100 * unseen_mask.mean()
            ) if len(evaluation) else 0.0,
        }

    return json_safe(
        {
            "numeric_psi": numeric,
            "categorical_unseen_values": categorical,
        }
    )


# ============================================================================
# BENCHMARK EACH SESSION DEFINITION
# ============================================================================

def benchmark_session_gap(
    frame: pd.DataFrame,
    gap_minutes: int,
    cutoff: pd.Timestamp,
) -> dict[str, Any]:
    train, evaluation, split_metadata = split_sessions(
        frame,
        gap_minutes,
        cutoff,
    )

    print(
        f"\n--- {gap_minutes}-minute sessions ---\n"
        f"Training: {len(train)} rows, "
        f"{split_metadata['training_sessions']} sessions, "
        f"{split_metadata['training_active_days']} active days\n"
        f"Evaluation: {len(evaluation)} rows, "
        f"{split_metadata['evaluation_sessions']} sessions, "
        f"{split_metadata['evaluation_active_days']} active days"
    )

    if len(train) < 100 or len(evaluation) < 20:
        raise ValueError(
            f"Insufficient rows for {gap_minutes}-minute grouping: "
            f"train={len(train)}, evaluation={len(evaluation)}."
        )

    x_train = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    x_eval = evaluation[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    # Isolation Forest
    forest_start = time.perf_counter()

    forest = make_isolation_forest()
    forest.fit(x_train)

    forest_runtime = time.perf_counter() - forest_start

    # Negate sklearn decision_function so higher means more anomalous.
    forest_train_scores = -forest.decision_function(x_train)
    forest_eval_scores = -forest.decision_function(x_eval)

    # Directional statistical baseline
    baseline_start = time.perf_counter()

    medians, scales, baseline_fit_report = fit_directional_baseline(train)

    baseline_train_scores, baseline_train_components = (
        score_directional_baseline(train, medians, scales)
    )
    baseline_eval_scores, baseline_eval_components = (
        score_directional_baseline(evaluation, medians, scales)
    )

    baseline_runtime = time.perf_counter() - baseline_start

    # Detector report
    detectors: dict[str, Any] = {}

    score_sets = {
        "isolation_forest": (
            forest_train_scores,
            forest_eval_scores,
        ),
        "directional_robust_baseline": (
            baseline_train_scores,
            baseline_eval_scores,
        ),
    }

    for detector_name, (train_scores, eval_scores) in score_sets.items():
        detectors[detector_name] = {
            "training_score_distribution": score_distribution(train_scores),
            "evaluation_score_distribution": score_distribution(eval_scores),
            "threshold_diagnostics": {
                f"{int(rate * 100)}%": threshold_report(
                    train_scores,
                    eval_scores,
                    rate,
                )
                for rate in ALERT_BUDGETS
            },
            "fixed_alert_budgets": {
                f"{int(rate * 100)}%": select_top_k(
                    evaluation,
                    eval_scores,
                    rate,
                )[0]
                for rate in ALERT_BUDGETS
            },
        }

    # Breakdown of directional baseline components on evaluation rows.
    component_report = {}

    for component_name, values in baseline_eval_components.items():
        component_report[component_name] = score_distribution(values)

    return json_safe(
        {
            "session_gap_minutes": gap_minutes,
            "split": split_metadata,
            "detectors": detectors,
            "ranking_agreement": compare_rankings(
                evaluation,
                forest_eval_scores,
                baseline_eval_scores,
            ),
            "directional_baseline_fit": baseline_fit_report,
            "directional_baseline_evaluation_components": component_report,
            "feature_drift": feature_drift_report(train, evaluation),
            "runtime_seconds": {
                "isolation_forest_fit_and_score": forest_runtime,
                "directional_baseline_fit_and_score": baseline_runtime,
            },
            "labels_available": False,
            "accuracy_metrics_available": False,
            "production_models_modified": False,
            "existing_risk_report_modified": False,
        }
    )


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    started = time.perf_counter()

    print("=" * 72)
    print("KBR FINAL ANOMALY DETECTOR BENCHMARK V5")
    print("=" * 72)

    business, dataset_metadata = load_business_dataset()
    features = build_causal_features(business)
    feature_validation = validate_features(features)

    print(f"Original dataset rows: {dataset_metadata['original_rows']}")
    print(f"HTTP rows excluded: {dataset_metadata['http_rows_excluded']}")
    print(f"Business rows used: {dataset_metadata['business_rows_used']}")
    print(f"Dataset SHA-256: {dataset_metadata['dataset_sha256']}")

    cutoff, cutoff_metadata = get_common_cutoff(features)
    print(f"Shared evaluation cutoff: {cutoff.isoformat()}")

    results: dict[str, Any] = {}

    for gap in SESSION_GAPS_MINUTES:
        results[str(gap)] = benchmark_session_gap(
            features,
            gap,
            cutoff,
        )

    total_runtime = time.perf_counter() - started

    report: dict[str, Any] = {
        "report_version": 5,
        "final_benchmark": True,
        "experiment": EXPERIMENT_NAME,
        "dataset": dataset_metadata,
        "feature_validation": feature_validation,
        "evaluation_method": {
            "session_gaps_minutes": SESSION_GAPS_MINUTES,
            "training_session_fraction": TRAINING_SESSION_FRACTION,
            "common_chronological_cutoff": cutoff_metadata,
            "session_leakage_check": (
                "Sessions crossing the cutoff are excluded; each retained "
                "session belongs to either training or evaluation."
            ),
            "isolation_forest": (
                "Isolation Forest fitted on training rows only; higher "
                "negated decision_function scores mean more anomalous."
            ),
            "directional_baseline": (
                "One-sided robust scores: shorter-than-usual gaps and "
                "higher rolling counts increase the score. Long gaps and "
                "low activity counts do not increase the score."
            ),
            "thresholds": (
                "Training score quantiles at nominal 1%, 2%, and 5% tails. "
                "Held-out alert rates are measured, not forced to match."
            ),
            "fixed_alert_budgets": (
                "Top-ranked 1%, 2%, and 5% of held-out rows, with stable "
                "row-order tie-breaking and explicit boundary tie counts."
            ),
        },
        "alert_budgets": ALERT_BUDGETS,
        "results_by_session_gap_minutes": results,
        "labels_available": False,
        "accuracy_metrics_available": False,
        "interpretation": (
            "This is an exploratory unsupervised benchmark, not a security "
            "validation. There are no verified anomaly labels. Ranking "
            "overlap, anomaly scores, PSI, and alert rates do not establish "
            "precision, recall, F1, or malicious activity. The evaluation "
            "window may contain only a few active days; interpret results "
            "accordingly. Production models and the existing risk report "
            "are not modified."
        ),
        "production_models_modified": False,
        "existing_risk_report_modified": False,
        "total_runtime_seconds": total_runtime,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Track a new MLflow run. No production model is saved or replaced.
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(
        run_name="final-business-detector-benchmark-v5"
    ) as run:
        report["mlflow_run_id"] = run.info.run_id

        mlflow.log_param("benchmark_version", 5)
        mlflow.log_param("final_benchmark", True)
        mlflow.log_param(
            "dataset_sha256",
            dataset_metadata["dataset_sha256"],
        )
        mlflow.log_param(
            "business_rows",
            dataset_metadata["business_rows_used"],
        )
        mlflow.log_param(
            "http_rows_excluded",
            dataset_metadata["http_rows_excluded"],
        )
        mlflow.log_param(
            "session_gaps_minutes",
            ",".join(map(str, SESSION_GAPS_MINUTES)),
        )
        mlflow.log_param(
            "common_evaluation_cutoff",
            cutoff.isoformat(),
        )
        mlflow.log_param("n_estimators", N_ESTIMATORS)
        mlflow.log_param("random_state", RANDOM_STATE)
        mlflow.log_param(
            "training_session_fraction",
            TRAINING_SESSION_FRACTION,
        )
        mlflow.log_param("labels_available", False)

        mlflow.log_metric(
            "business_rows",
            dataset_metadata["business_rows_used"],
        )
        mlflow.log_metric(
            "total_runtime_seconds",
            total_runtime,
        )

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
                    f"{detector_prefix}_evaluation_unique_scores",
                    detector_report[
                        "evaluation_score_distribution"
                    ]["unique_exact_scores"],
                )

                mlflow.log_metric(
                    f"{detector_prefix}_evaluation_score_p95",
                    detector_report[
                        "evaluation_score_distribution"
                    ]["p95"],
                )

                for budget, alert_report in (
                    detector_report["fixed_alert_budgets"].items()
                ):
                    budget_tag = budget.replace("%", "pct")

                    mlflow.log_metric(
                        f"{detector_prefix}_top_{budget_tag}_count",
                        alert_report["selected_count"],
                    )

            for budget, agreement in (
                gap_report["ranking_agreement"].items()
            ):
                budget_tag = budget.replace("%", "pct")

                mlflow.log_metric(
                    f"{prefix}_ranking_jaccard_{budget_tag}",
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
    print("FINAL BENCHMARK V5 COMPLETED")
    print("=" * 72)

    for gap, gap_report in results.items():
        split = gap_report["split"]

        print(f"\nSession gap: {gap} minute(s)")
        print(
            f"Train: {split['training_rows']} rows, "
            f"{split['training_active_days']} active days"
        )
        print(
            f"Eval:  {split['evaluation_rows']} rows, "
            f"{split['evaluation_active_days']} active days"
        )

        for detector_name, detector_report in (
            gap_report["detectors"].items()
        ):
            distribution = detector_report[
                "evaluation_score_distribution"
            ]

            print(f"\n{detector_name}")
            print(
                f"  Unique evaluation scores: "
                f"{distribution['unique_exact_scores']}"
            )
            print(f"  Evaluation p95: {distribution['p95']:.6f}")
            print(f"  Zero-score rows: {distribution['zero_score_count']}")

            for budget, alert_report in (
                detector_report["fixed_alert_budgets"].items()
            ):
                print(
                    f"  Top {budget}: {alert_report['selected_count']} alerts; "
                    f"boundary ties="
                    f"{alert_report['rows_tied_at_selection_boundary']}"
                )

        print("\nRanking agreement:")
        for budget, agreement in gap_report["ranking_agreement"].items():
            print(
                f"  {budget}: overlap={agreement['overlap_count']}, "
                f"Jaccard={agreement['jaccard_pct']:.2f}%"
            )

    print(f"\nReport: {REPORT_PATH}")
    print(f"MLflow run ID: {report['mlflow_run_id']}")
    print("Production models modified: False")
    print("Existing risk report modified: False")


if __name__ == "__main__":
    main()