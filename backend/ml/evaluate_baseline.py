from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.ml.anomaly_detection import (
    BUSINESS_CATEGORICAL_FEATURES,
    BUSINESS_NUMERIC_FEATURES,
    HTTP_CATEGORICAL_FEATURES,
    HTTP_NUMERIC_FEATURES,
    calculate_distribution_summary,
    calibrate_threshold,
    create_preprocessor,
)
from backend.ml.features.activity_features import (
    build_activity_feature_dataset,
)

REPORT_PATH = Path("data/reports/baseline_evaluation_report.json")

TRAIN_FRACTION = 0.80
THRESHOLD_PERCENTILE = 95.0
N_ESTIMATORS = 300
RANDOM_STATE = 42
TIME_WINDOWS = 4

# These are discrete/calendar features, not continuous measurements.
DISCRETE_NUMERIC_FEATURES = {
    "hour",
    "day_of_week",
    "is_weekend",
    "status_code",
    "is_error_status",
    "is_auth_failure",
    "query_parameter_count",
}


def calculate_psi(
    training: pd.Series,
    evaluation: pd.Series,
    bins: int = 10,
) -> float | None:
    """PSI using training quantile bins; descriptive, not a hypothesis test."""
    train = pd.to_numeric(training, errors="coerce").dropna().to_numpy()
    test = pd.to_numeric(evaluation, errors="coerce").dropna().to_numpy()

    if len(train) == 0 or len(test) == 0:
        return None

    quantiles = np.linspace(0, 1, bins + 1)[1:-1]
    inner_edges = np.unique(np.quantile(train, quantiles))
    edges = np.concatenate(([-np.inf], inner_edges, [np.inf]))

    train_counts = np.histogram(train, bins=edges)[0].astype(float)
    test_counts = np.histogram(test, bins=edges)[0].astype(float)

    smoothing = 1e-6
    train_pct = (train_counts + smoothing) / (
        train_counts.sum() + smoothing * len(train_counts)
    )
    test_pct = (test_counts + smoothing) / (
        test_counts.sum() + smoothing * len(test_counts)
    )

    value = np.sum((test_pct - train_pct) * np.log(test_pct / train_pct))
    return round(float(value), 6)


def categorical_drift(
    training: pd.Series,
    evaluation: pd.Series,
) -> dict:
    """Compare discrete category distributions, including unseen values."""
    train = training.fillna("UNKNOWN").astype(str)
    test = evaluation.fillna("UNKNOWN").astype(str)

    categories = sorted(set(train) | set(test))
    smoothing = 1e-6

    train_counts = train.value_counts().reindex(categories, fill_value=0).to_numpy(float)
    test_counts = test.value_counts().reindex(categories, fill_value=0).to_numpy(float)

    train_pct = (train_counts + smoothing) / (
        train_counts.sum() + smoothing * len(categories)
    )
    test_pct = (test_counts + smoothing) / (
        test_counts.sum() + smoothing * len(categories)
    )

    psi = np.sum((test_pct - train_pct) * np.log(test_pct / train_pct))
    unseen_mask = ~test.isin(set(train))

    return {
        "training_unique_values": int(train.nunique()),
        "evaluation_unique_values": int(test.nunique()),
        "unseen_evaluation_rows": int(unseen_mask.sum()),
        "unseen_evaluation_percentage": round(float(unseen_mask.mean() * 100), 2),
        "distribution_psi": round(float(psi), 6),
    }


def timeline_summary(frame: pd.DataFrame) -> dict:
    """Describe temporal coverage and event concentration."""
    ordered = frame.sort_values("occurred_at").copy()
    timestamps = ordered["occurred_at"]
    gaps = timestamps.diff().dt.total_seconds().dropna()

    daily = (
        ordered.set_index("occurred_at")
        .resample("1D")
        .size()
    )
    daily = daily[daily > 0]

    rolling = (
        pd.Series(
            1,
            index=pd.DatetimeIndex(timestamps),
            dtype="int64",
        )
        .sort_index()
        .rolling("5min")
        .sum()
    )

    return {
        "rows": int(len(ordered)),
        "start": str(timestamps.min()),
        "end": str(timestamps.max()),
        "active_calendar_days": int(len(daily)),
        "daily_counts": {
            str(day.date()): int(count)
            for day, count in daily.items()
        },
        "inter_event_gap_seconds": {
            "median": round(float(gaps.median()), 3) if not gaps.empty else None,
            "p95": round(float(gaps.quantile(0.95)), 3) if not gaps.empty else None,
            "maximum": round(float(gaps.max()), 3) if not gaps.empty else None,
        },
        "maximum_rolling_5min_events": int(rolling.max()) if not rolling.empty else 0,
    }


def evaluate_population(
    frame: pd.DataFrame,
    *,
    population: str,
    numeric_features: list[str],
    categorical_features: list[str],
) -> dict:
    frame = frame.sort_values("occurred_at").reset_index(drop=True).copy()

    if len(frame) < 10:
        raise ValueError(f"{population}: not enough rows to evaluate.")

    split_index = max(1, min(int(len(frame) * TRAIN_FRACTION), len(frame) - 1))
    training = frame.iloc[:split_index].copy()
    evaluation = frame.iloc[split_index:].copy()

    feature_columns = numeric_features + categorical_features
    preprocessor = create_preprocessor(numeric_features, categorical_features)

    X_train = preprocessor.fit_transform(training[feature_columns])
    X_eval = preprocessor.transform(evaluation[feature_columns])

    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train)

    train_scores = pd.Series(
        -model.decision_function(X_train), dtype="float64"
    )
    eval_scores = pd.Series(
        -model.decision_function(X_eval), dtype="float64"
    )

    threshold = calibrate_threshold(
        train_scores,
        percentile=THRESHOLD_PERCENTILE,
    )
    flags = eval_scores >= threshold

    # Split evaluation into equal elapsed-time intervals, not equal row counts.
    start = evaluation["occurred_at"].min()
    end = evaluation["occurred_at"].max()
    boundaries = pd.to_datetime(
        np.linspace(start.value, end.value, TIME_WINDOWS + 1),
        utc=True,
    )

    windows = []
    for index in range(TIME_WINDOWS):
        lower = boundaries[index]
        upper = boundaries[index + 1]

        if index == TIME_WINDOWS - 1:
            mask = (
                (evaluation["occurred_at"] >= lower)
                & (evaluation["occurred_at"] <= upper)
            )
        else:
            mask = (
                (evaluation["occurred_at"] >= lower)
                & (evaluation["occurred_at"] < upper)
            )

        selected = np.flatnonzero(mask.to_numpy())
        window_scores = eval_scores.iloc[selected]
        window_flags = flags.iloc[selected]

        windows.append({
            "window": index + 1,
            "start": str(lower),
            "end": str(upper),
            "rows": int(len(selected)),
            "anomaly_count": int(window_flags.sum()),
            "anomaly_percentage": (
                round(float(window_flags.mean() * 100), 2)
                if len(selected) else None
            ),
            "score_distribution": (
                calculate_distribution_summary(window_scores)
                if len(selected) else None
            ),
        })

    continuous_features = [
        column for column in numeric_features
        if column not in DISCRETE_NUMERIC_FEATURES
    ]
    discrete_features = [
        column for column in numeric_features
        if column in DISCRETE_NUMERIC_FEATURES
    ]

    continuous_drift = {
        column: calculate_psi(training[column], evaluation[column])
        for column in continuous_features
    }
    valid_psi = [value for value in continuous_drift.values() if value is not None]

    categorical_drift = {
        column: categorical_drift_fn(training[column], evaluation[column])
        for column in categorical_features + discrete_features
    }

    return {
        "population": population,
        "methodology": {
            "split": "chronological by row timestamp",
            "training_fraction": TRAIN_FRACTION,
            "threshold_percentile": THRESHOLD_PERCENTILE,
            "n_estimators": N_ESTIMATORS,
            "random_state": RANDOM_STATE,
            "model_saved": False,
            "evaluation_windows": (
                f"{TIME_WINDOWS} equal-duration calendar intervals"
            ),
        },
        "training": {
            "rows": int(len(training)),
            "timeline": timeline_summary(training),
            "score_distribution": calculate_distribution_summary(train_scores),
        },
        "evaluation": {
            "rows": int(len(evaluation)),
            "timeline": timeline_summary(evaluation),
            "score_distribution": calculate_distribution_summary(eval_scores),
            "anomaly_count": int(flags.sum()),
            "anomaly_percentage": round(float(flags.mean() * 100), 2),
            "threshold": round(float(threshold), 6),
            "windows": windows,
        },
        "score_distribution_shift": {
            "mean_delta": round(float(eval_scores.mean() - train_scores.mean()), 6),
            "median_delta": round(float(eval_scores.median() - train_scores.median()), 6),
            "p95_delta": round(
                float(eval_scores.quantile(0.95) - train_scores.quantile(0.95)),
                6,
            ),
        },
        "continuous_feature_drift": {
            "method": "PSI using training quantile bins",
            "mean_psi": round(float(np.mean(valid_psi)), 6) if valid_psi else None,
            "features": continuous_drift,
            "interpretation": (
                "PSI is a descriptive indicator. Common thresholds (<0.10, "
                "0.10-0.25, >0.25) are heuristics, not statistical tests."
            ),
        },
        "discrete_and_categorical_drift": categorical_drift,
        "limitations": [
            "No labeled incidents are available; precision, recall, F1 and accuracy cannot be calculated.",
            "Anomaly scores indicate deviation from learned patterns, not proof of malicious activity.",
            "The evaluation is later data from the same dataset, not an independent external test.",
            "Equal-duration windows may contain very different numbers of events.",
            "Large temporal gaps and concentrated bursts can dominate these results.",
            "The evaluation model is not saved and does not replace the dashboard model.",
        ],
    }


# Avoid shadowing the function name inside the dictionary comprehension.
categorical_drift_fn = categorical_drift


def main() -> None:
    print("=" * 72)
    print("KBR BASELINE EVALUATION")
    print("=" * 72)

    features = build_activity_feature_dataset()

    populations = [
        (
            "http",
            features[features["is_http_request"] == 1].copy(),
            HTTP_NUMERIC_FEATURES,
            HTTP_CATEGORICAL_FEATURES,
        ),
        (
            "business",
            features[features["is_http_request"] == 0].copy(),
            BUSINESS_NUMERIC_FEATURES,
            BUSINESS_CATEGORICAL_FEATURES,
        ),
    ]

    results = {}
    for name, frame, numeric, categorical in populations:
        print(f"\nEvaluating {name}: {len(frame)} rows")
        report = evaluate_population(
            frame,
            population=name,
            numeric_features=numeric,
            categorical_features=categorical,
        )
        results[name] = report

        print("  Training rows:", report["training"]["rows"])
        print("  Evaluation rows:", report["evaluation"]["rows"])
        print("  Anomaly rate:", report["evaluation"]["anomaly_percentage"], "%")
        print(
            "  Maximum rolling five-minute events:",
            report["evaluation"]["timeline"]["maximum_rolling_5min_events"],
        )
        print(
            "  Mean continuous-feature PSI:",
            report["continuous_feature_drift"]["mean_psi"],
        )
        print("  Time-window anomaly rates:")
        for window in report["evaluation"]["windows"]:
            rate = window["anomaly_percentage"]
            print(
                f"    Window {window['window']}: "
                f"{window['rows']} rows, "
                f"{rate if rate is not None else 'no events'}"
            )

    output = {
        "report_version": 1,
        "model_type": "IsolationForest",
        "purpose": "Temporal baseline, anomaly stability and drift diagnostics",
        "total_rows": int(len(features)),
        "http_rows": int((features["is_http_request"] == 1).sum()),
        "business_rows": int((features["is_http_request"] == 0).sum()),
        "existing_models_modified": False,
        "existing_risk_report_modified": False,
        "populations": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(output, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"\nReport written to: {REPORT_PATH}")
    print("Existing model bundles and risk report were not modified.")


if __name__ == "__main__":
    main()
