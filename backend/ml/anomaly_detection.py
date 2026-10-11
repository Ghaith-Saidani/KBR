from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder

from backend.ml.features.activity_features import (
    build_activity_feature_dataset,
)


MODEL_DIR = Path("data/models")
REPORT_DIR = Path("data/reports")

HTTP_MODEL_PATH = MODEL_DIR / "http_anomaly_detector.joblib"
BUSINESS_MODEL_PATH = MODEL_DIR / "business_anomaly_detector.joblib"
REPORT_PATH = REPORT_DIR / "anomaly_detection_report.json"


NUMERIC_FEATURES = [
    "hour",
    "day_of_week",
    "is_weekend",
    "activity_count_5m",
    "activity_count_1h",
    "activity_count_24h",
    "log_time_since_previous_activity",
    "user_activity_count_1h",
    "user_activity_count_24h",
]


HTTP_NUMERIC_FEATURES = [
    *NUMERIC_FEATURES,
    "status_code",
    "is_error_status",
    "is_auth_failure",
    "query_parameter_count",
]


HTTP_CATEGORICAL_FEATURES = [
    "method",
    "endpoint_normalized",
]


BUSINESS_CATEGORICAL_FEATURES = [
    "action",
    "resource_type",
]


BUSINESS_NUMERIC_FEATURES = [
    *NUMERIC_FEATURES,
]


def create_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                numeric_features,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
    )


def calculate_distribution_summary(
    scores: pd.Series,
) -> dict:
    if scores.empty:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "p90": None,
            "p95": None,
            "p99": None,
        }

    return {
        "count": int(len(scores)),
        "min": round(float(scores.min()), 6),
        "max": round(float(scores.max()), 6),
        "mean": round(float(scores.mean()), 6),
        "median": round(float(scores.median()), 6),
        "std": round(float(scores.std()), 6),
        "p90": round(float(scores.quantile(0.90)), 6),
        "p95": round(float(scores.quantile(0.95)), 6),
        "p99": round(float(scores.quantile(0.99)), 6),
    }


def calculate_distribution_shift(
    train_scores: pd.Series,
    evaluation_scores: pd.Series,
) -> dict:
    if train_scores.empty or evaluation_scores.empty:
        return {
            "mean_delta": None,
            "median_delta": None,
            "p95_delta": None,
            "std_delta": None,
        }

    return {
        "mean_delta": round(
            float(
                evaluation_scores.mean()
                - train_scores.mean()
            ),
            6,
        ),
        "median_delta": round(
            float(
                evaluation_scores.median()
                - train_scores.median()
            ),
            6,
        ),
        "p95_delta": round(
            float(
                evaluation_scores.quantile(0.95)
                - train_scores.quantile(0.95)
            ),
            6,
        ),
        "std_delta": round(
            float(
                evaluation_scores.std()
                - train_scores.std()
            ),
            6,
        ),
    }


def calibrate_threshold(
    training_scores: pd.Series,
    *,
    percentile: float = 95.0,
) -> float:
    if training_scores.empty:
        raise ValueError(
            "Cannot calibrate an anomaly threshold "
            "without training scores."
        )

    if not 0 < percentile < 100:
        raise ValueError(
            "Threshold percentile must be between 0 and 100."
        )

    return float(
        training_scores.quantile(
            percentile / 100.0
        )
    )


def build_top_anomalies(
    results: pd.DataFrame,
) -> list[dict]:
    top = (
        results.head(10)
        .drop(
            columns=[
                "is_anomaly",
                "anomaly_score_ratio",
            ],
            errors="ignore",
        )
        .copy()
    )

    if "occurred_at" in top.columns:
        top["occurred_at"] = (
            top["occurred_at"].astype(str)
        )

    return top.to_dict(
        orient="records"
    )


def train_detector(
    df: pd.DataFrame,
    *,
    model_path: Path,
    numeric_features: list[str],
    categorical_features: list[str],
    random_state: int = 42,
    threshold_percentile: float = 95.0,
) -> tuple[dict, pd.DataFrame]:
    if df.empty:
        raise ValueError(
            "Cannot train an anomaly detector "
            "on an empty dataset."
        )

    required = set(
        numeric_features
        + categorical_features
        + [
            "id",
            "occurred_at",
        ]
    )

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Missing model features: "
            + ", ".join(sorted(missing))
        )

    work = df.copy()

    # Ensure chronological ordering.
    work = (
        work.sort_values("occurred_at")
        .reset_index(drop=True)
    )

    if len(work) < 2:
        raise ValueError(
            "At least two rows are required "
            "for a train/evaluation split."
        )

    # ---------------------------------------------------------
    # Time-based split
    #
    # 80% oldest observations -> training
    # 20% newest observations -> evaluation
    # ---------------------------------------------------------

    split_index = max(
        1,
        int(len(work) * 0.80),
    )

    if split_index >= len(work):
        split_index = len(work) - 1

    train_df = work.iloc[
        :split_index
    ].copy()

    test_df = work.iloc[
        split_index:
    ].copy()

    # ---------------------------------------------------------
    # Preprocessing
    # ---------------------------------------------------------

    preprocessor = create_preprocessor(
        numeric_features,
        categorical_features,
    )

    feature_columns = (
        numeric_features
        + categorical_features
    )

    X_train = preprocessor.fit_transform(
        train_df[feature_columns]
    )

    X_test = preprocessor.transform(
        test_df[feature_columns]
    )

    # ---------------------------------------------------------
    # Isolation Forest
    #
    # contamination is NOT used as the evaluation criterion.
    #
    # We let Isolation Forest learn its representation and
    # calibrate our own threshold from historical training
    # scores below.
    # ---------------------------------------------------------

    model = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(X_train)

    # ---------------------------------------------------------
    # Convert sklearn scores into:
    #
    # higher score = more anomalous
    # ---------------------------------------------------------

    train_scores = pd.Series(
        -model.decision_function(X_train),
        index=train_df.index,
        dtype="float64",
    )

    evaluation_scores = pd.Series(
        -model.decision_function(X_test),
        index=test_df.index,
        dtype="float64",
    )

    # ---------------------------------------------------------
    # Threshold calibration
    #
    # 95th percentile of historical training anomaly scores.
    #
    # This means the detector flags observations that are more
    # anomalous than approximately 95% of historical training
    # observations.
    # ---------------------------------------------------------

    threshold = calibrate_threshold(
        train_scores,
        percentile=threshold_percentile,
    )

    # ---------------------------------------------------------
    # Evaluation results
    # ---------------------------------------------------------

    results = test_df[
        [
            "id",
            "occurred_at",
        ]
        + numeric_features
        + categorical_features
    ].copy()

    results["anomaly_score"] = (
        evaluation_scores.values
    )

    results["is_anomaly"] = (
        results["anomaly_score"]
        >= threshold
    ).astype(int)

    # A score ratio above 1 means the observation is above
    # the calibrated anomaly threshold.
    #
    # Example:
    #   1.00 -> exactly at threshold
    #   1.50 -> 50% above threshold
    #   2.00 -> twice the threshold
    #
    # For negative thresholds this ratio is not meaningful,
    # so we fall back to a score delta.
    if threshold > 0:
        results["anomaly_score_ratio"] = (
            results["anomaly_score"]
            / threshold
        )
    else:
        results["anomaly_score_ratio"] = (
            results["anomaly_score"]
            - threshold
        )

    results["model_population"] = (
        "http"
        if "status_code" in numeric_features
        else "business"
    )

    results = results.sort_values(
        "anomaly_score",
        ascending=False,
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # Distribution analysis
    # ---------------------------------------------------------

    train_distribution = (
        calculate_distribution_summary(
            train_scores
        )
    )

    evaluation_distribution = (
        calculate_distribution_summary(
            evaluation_scores
        )
    )

    distribution_shift = (
        calculate_distribution_shift(
            train_scores,
            evaluation_scores,
        )
    )

    anomaly_count = int(
        results["is_anomaly"].sum()
    )

    evaluation_count = len(results)

    anomaly_percentage = (
        anomaly_count
        / evaluation_count
        * 100
        if evaluation_count
        else 0.0
    )

    # ---------------------------------------------------------
    # Save model bundle
    # ---------------------------------------------------------

    model_bundle = {
        "model": model,
        "preprocessor": preprocessor,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "training_rows": len(train_df),
        "evaluation_rows": len(test_df),
        "random_state": random_state,
        "threshold": threshold,
        "threshold_percentile": threshold_percentile,
        "threshold_method": (
            "training_score_percentile"
        ),
    }

    model_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model_bundle,
        model_path,
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    report = {
        "training_rows": len(train_df),
        "evaluation_rows": len(test_df),
        "feature_count_before_encoding": (
            len(numeric_features)
            + len(categorical_features)
        ),
        "encoded_feature_count": int(
            X_train.shape[1]
        ),
        "threshold": round(
            threshold,
            6,
        ),
        "threshold_method": (
            "95th percentile of historical "
            "training anomaly scores"
        ),
        "threshold_percentile": (
            threshold_percentile
        ),
        "anomaly_count": anomaly_count,
        "anomaly_percentage": round(
            anomaly_percentage,
            2,
        ),
        "training_score_distribution": (
            train_distribution
        ),
        "evaluation_score_distribution": (
            evaluation_distribution
        ),
        "distribution_shift": (
            distribution_shift
        ),
        "score_min": round(
            float(evaluation_scores.min()),
            6,
        ),
        "score_max": round(
            float(evaluation_scores.max()),
            6,
        ),
        "score_mean": round(
            float(evaluation_scores.mean()),
            6,
        ),
        "score_median": round(
            float(evaluation_scores.median()),
            6,
        ),
        "top_anomalies": build_top_anomalies(
            results
        ),
    }

    return report, results


def print_detector_summary(
    label: str,
    report: dict,
) -> None:
    print(
        f"\n{label} training rows: "
        f"{report['training_rows']}"
    )

    print(
        f"{label} evaluation rows: "
        f"{report['evaluation_rows']}"
    )

    print(
        f"{label} threshold: "
        f"{report['threshold']}"
    )

    print(
        f"{label} anomalies: "
        f"{report['anomaly_count']} "
        f"({report['anomaly_percentage']}%)"
    )

    training_distribution = (
        report["training_score_distribution"]
    )

    evaluation_distribution = (
        report["evaluation_score_distribution"]
    )

    print(
        f"{label} training score mean: "
        f"{training_distribution['mean']}"
    )

    print(
        f"{label} evaluation score mean: "
        f"{evaluation_distribution['mean']}"
    )

    print(
        f"{label} evaluation p95: "
        f"{evaluation_distribution['p95']}"
    )

    shift = report["distribution_shift"]

    print(
        f"{label} mean distribution shift: "
        f"{shift['mean_delta']}"
    )


def main() -> None:
    print("=" * 70)
    print("KBR ML ANOMALY DETECTION")
    print("=" * 70)

    print("\n[1/4] Building feature dataset...")

    features = (
        build_activity_feature_dataset()
    )

    print(
        f"Feature rows: {len(features)}"
    )

    print("\n[2/4] Splitting populations...")

    http_df = features[
        features["is_http_request"] == 1
    ].copy()

    business_df = features[
        features["is_http_request"] == 0
    ].copy()

    print(
        f"HTTP activities:      {len(http_df)}"
    )

    print(
        f"Business activities:  {len(business_df)}"
    )

    print("\n[3/4] Training HTTP detector...")

    http_report, http_results = (
        train_detector(
            http_df,
            model_path=HTTP_MODEL_PATH,
            numeric_features=HTTP_NUMERIC_FEATURES,
            categorical_features=HTTP_CATEGORICAL_FEATURES,
        )
    )

    print_detector_summary(
        "HTTP",
        http_report,
    )

    print("\nTop HTTP anomalies:")

    print(
        http_results[
            [
                "occurred_at",
                "anomaly_score",
                "status_code",
                "is_error_status",
                "is_auth_failure",
                "method",
                "endpoint_normalized",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nTraining business detector...")

    business_report, business_results = (
        train_detector(
            business_df,
            model_path=BUSINESS_MODEL_PATH,
            numeric_features=BUSINESS_NUMERIC_FEATURES,
            categorical_features=BUSINESS_CATEGORICAL_FEATURES,
        )
    )

    print_detector_summary(
        "Business",
        business_report,
    )

    print("\nTop business anomalies:")

    print(
        business_results[
            [
                "occurred_at",
                "anomaly_score",
                "action",
                "resource_type",
                "activity_count_5m",
                "activity_count_1h",
                "user_activity_count_1h",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\n[4/4] Writing report...")

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined_report = {
        "model_type": "IsolationForest",
        "description": (
            "Separate unsupervised anomaly detectors "
            "for HTTP and business activities. "
            "Anomaly thresholds are calibrated from "
            "historical training score distributions."
        ),
        "total_rows": len(features),
        "http_rows": len(http_df),
        "business_rows": len(business_df),
        "http_model": http_report,
        "business_model": business_report,
    }

    REPORT_PATH.write_text(
        json.dumps(
            combined_report,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print(
        f"Report: {REPORT_PATH}"
    )

    print(
        f"HTTP model: {HTTP_MODEL_PATH}"
    )

    print(
        f"Business model: {BUSINESS_MODEL_PATH}"
    )

    print("\n" + "=" * 70)
    print("ANOMALY DETECTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()