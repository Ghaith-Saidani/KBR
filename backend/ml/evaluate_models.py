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

REPORT_PATH = Path("data/reports/model_evaluation_report.json")

TRAIN_FRACTION = 0.80
THRESHOLD_PERCENTILE = 95.0
RANDOM_STATE = 42
N_ESTIMATORS = 300
EVALUATION_WINDOWS = 4


def calculate_psi(
    training: pd.Series,
    evaluation: pd.Series,
) -> float | None:
    """Calculate population stability index using training quantile bins."""
    train = pd.to_numeric(training, errors="coerce").dropna()
    test = pd.to_numeric(evaluation, errors="coerce").dropna()

    if train.empty or test.empty:
        return None

    quantiles = train.quantile(
        [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
    ).to_numpy()

    edges = np.unique(
        np.concatenate(([-np.inf], quantiles, [np.inf]))
    )

    train_counts = np.histogram(train.to_numpy(), bins=edges)[0]
    test_counts = np.histogram(test.to_numpy(), bins=edges)[0]

    # Smoothing avoids zero proportions and undefined logarithms.
    smoothing = 1e-6

    train_pct = (
        train_counts + smoothing
    ) / (train_counts.sum() + smoothing * len(train_counts))

    test_pct = (
        test_counts + smoothing
    ) / (test_counts.sum() + smoothing * len(test_counts))

    psi = np.sum(
        (test_pct - train_pct)
        * np.log(test_pct / train_pct)
    )

    return round(float(psi), 6)


def calculate_unseen_categories(
    training: pd.DataFrame,
    evaluation: pd.DataFrame,
    categorical_features: list[str],
) -> dict:
    """Measure evaluation categories absent from the training period."""
    report = {}

    for column in categorical_features:
        known = set(training[column].fillna("UNKNOWN").astype(str))
        values = evaluation[column].fillna("UNKNOWN").astype(str)

        unseen_mask = ~values.isin(known)

        report[column] = {
            "training_unique_values": len(known),
            "evaluation_unique_values": int(values.nunique()),
            "unseen_evaluation_rows": int(unseen_mask.sum()),
            "unseen_evaluation_percentage": round(
                float(unseen_mask.mean() * 100), 2
            ),
        }

    return report


def evaluate_population(
    frame: pd.DataFrame,
    *,
    population: str,
    numeric_features: list[str],
    categorical_features: list[str],
) -> dict:
    """Fit on the oldest observations and evaluate on newer observations."""
    if frame.empty:
        raise ValueError(f"{population}: dataset is empty.")

    required = {
        "id",
        "occurred_at",
        *numeric_features,
        *categorical_features,
    }
    missing = required - set(frame.columns)

    if missing:
        raise ValueError(
            f"{population}: missing columns: {', '.join(sorted(missing))}"
        )

    work = (
        frame.sort_values("occurred_at")
        .reset_index(drop=True)
        .copy()
    )

    if work["occurred_at"].isna().any():
        raise ValueError(f"{population}: invalid timestamps detected.")

    if len(work) < 10:
        raise ValueError(
            f"{population}: at least 10 rows are required; got {len(work)}."
        )

    split_index = int(len(work) * TRAIN_FRACTION)
    split_index = max(1, min(split_index, len(work) - 1))

    training = work.iloc[:split_index].copy()
    evaluation = work.iloc[split_index:].copy()

    feature_columns = numeric_features + categorical_features

    preprocessor = create_preprocessor(
        numeric_features,
        categorical_features,
    )

    X_train = preprocessor.fit_transform(training[feature_columns])
    X_evaluation = preprocessor.transform(evaluation[feature_columns])

    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train)

    # Higher values represent more anomalous observations.
    train_scores = pd.Series(
        -model.decision_function(X_train),
        dtype="float64",
    )
    evaluation_scores = pd.Series(
        -model.decision_function(X_evaluation),
        dtype="float64",
    )

    threshold = calibrate_threshold(
        train_scores,
        percentile=THRESHOLD_PERCENTILE,
    )

    evaluation_flags = evaluation_scores >= threshold

    # Divide the evaluation period into chronological, contiguous windows.
    window_reports = []
    positions = np.array_split(
        np.arange(len(evaluation)),
        min(EVALUATION_WINDOWS, len(evaluation)),
    )

    for window_number, indexes in enumerate(positions, start=1):
        if len(indexes) == 0:
            continue

        window_scores = evaluation_scores.iloc[indexes]
        window_flags = window_scores >= threshold
        timestamps = evaluation.iloc[indexes]["occurred_at"]

        window_reports.append({
            "window": window_number,
            "rows": int(len(indexes)),
            "start": str(timestamps.min()),
            "end": str(timestamps.max()),
            "anomaly_count": int(window_flags.sum()),
            "anomaly_percentage": round(
                float(window_flags.mean() * 100), 2
            ),
            "score_distribution": calculate_distribution_summary(
                window_scores
            ),
        })

    numeric_drift = {
        column: calculate_psi(
            training[column],
            evaluation[column],
        )
        for column in numeric_features
    }

    # PSI is a drift indicator, not a model accuracy metric.
    valid_psi = [
        value for value in numeric_drift.values()
        if value is not None
    ]

    mean_psi = (
        round(float(np.mean(valid_psi)), 6)
        if valid_psi else None
    )

    unseen_categories = calculate_unseen_categories(
        training,
        evaluation,
        categorical_features,
    )

    unseen_rows = int(
        sum(
            item["unseen_evaluation_rows"]
            for item in unseen_categories.values()
        )
    )

    evaluation_category_checks = (
        len(evaluation) * len(categorical_features)
    )

    return {
        "population": population,
        "methodology": {
            "split": "chronological",
            "training_fraction": TRAIN_FRACTION,
            "threshold_percentile": THRESHOLD_PERCENTILE,
            "random_state": RANDOM_STATE,
            "n_estimators": N_ESTIMATORS,
            "model_saved": False,
        },
        "training": {
            "rows": int(len(training)),
            "start": str(training["occurred_at"].min()),
            "end": str(training["occurred_at"].max()),
            "score_distribution": calculate_distribution_summary(
                train_scores
            ),
        },
        "evaluation": {
            "rows": int(len(evaluation)),
            "start": str(evaluation["occurred_at"].min()),
            "end": str(evaluation["occurred_at"].max()),
            "score_distribution": calculate_distribution_summary(
                evaluation_scores
            ),
            "anomaly_count": int(evaluation_flags.sum()),
            "anomaly_percentage": round(
                float(evaluation_flags.mean() * 100), 2
            ),
            "threshold": round(float(threshold), 6),
            "windows": window_reports,
        },
        "score_distribution_shift": {
            "mean_delta": round(
                float(evaluation_scores.mean() - train_scores.mean()), 6
            ),
            "median_delta": round(
                float(evaluation_scores.median() - train_scores.median()), 6
            ),
            "p95_delta": round(
                float(
                    evaluation_scores.quantile(0.95)
                    - train_scores.quantile(0.95)
                ),
                6,
            ),
        },
        "numeric_feature_drift": {
            "method": "population stability index (PSI)",
            "mean_psi": mean_psi,
            "features": numeric_drift,
            "interpretation": (
                "PSI is a descriptive drift indicator. Common rules of "
                "thumb are below 0.10 for limited drift, 0.10-0.25 for "
                "moderate drift, and above 0.25 for substantial drift. "
                "These thresholds are heuristics, not statistical tests."
            ),
        },
        "categorical_generalization": {
            "feature_count": len(categorical_features),
            "unseen_category_checks": unseen_categories,
            "total_unseen_feature_values": unseen_rows,
            "total_evaluation_category_checks": (
                evaluation_category_checks
            ),
            "unseen_percentage_of_category_checks": round(
                100 * unseen_rows / evaluation_category_checks, 2
            ) if evaluation_category_checks else 0.0,
        },
        "limitations": [
            "No labeled incidents are available, so precision, recall, "
            "F1 and classification accuracy cannot be calculated.",
            "Anomalies are deviations from learned behavior, not proof "
            "of malicious activity.",
            "The chronological split evaluates later observations from "
            "the same dataset; it is not an independent external test.",
            "Feature drift and score stability do not establish that "
            "the detector is operationally useful.",
        ],
    }


def main() -> None:
    print("=" * 72)
    print("KBR ML MODEL EVALUATION")
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

    reports = {}

    for name, frame, numeric, categorical in populations:
        print(f"\nEvaluating {name} population ({len(frame)} rows)...")

        report = evaluate_population(
            frame,
            population=name,
            numeric_features=numeric,
            categorical_features=categorical,
        )
        reports[name] = report

        evaluation = report["evaluation"]
        print(f"  Training rows: {report['training']['rows']}")
        print(f"  Evaluation rows: {evaluation['rows']}")
        print(f"  Threshold: {evaluation['threshold']}")
        print(
            f"  Evaluation anomalies: {evaluation['anomaly_count']} "
            f"({evaluation['anomaly_percentage']}%)"
        )
        print(
            "  Mean score delta: "
            f"{report['score_distribution_shift']['mean_delta']}"
        )
        print(
            "  Mean numeric PSI: "
            f"{report['numeric_feature_drift']['mean_psi']}"
        )
        print(
            "  Unseen category checks: "
            f"{report['categorical_generalization']['unseen_percentage_of_category_checks']}%"
        )

        print("  Anomaly rate by evaluation window:")
        for window in evaluation["windows"]:
            print(
                f"    Window {window['window']}: "
                f"{window['anomaly_count']}/{window['rows']} "
                f"({window['anomaly_percentage']}%)"
            )

    output = {
        "report_version": 1,
        "model_type": "IsolationForest",
        "purpose": "Unsupervised chronological evaluation and drift diagnostics",
        "total_rows": int(len(features)),
        "http_rows": int((features["is_http_request"] == 1).sum()),
        "business_rows": int((features["is_http_request"] == 0).sum()),
        "models_overwritten": False,
        "existing_risk_report_modified": False,
        "populations": reports,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(output, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"\nEvaluation report written to: {REPORT_PATH}")
    print("Existing model bundles and risk report were not modified.")


if __name__ == "__main__":
    main()
