from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# Run from the KBR project root:
# python backend/ml/analyze_v5_categorical_ablation.py

ROOT = Path.cwd()
ML_DIR = ROOT / "backend" / "ml"
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

import benchmark_business_detectors_v5 as v5  # noqa: E402


REPORT_DIR = ROOT / "data" / "reports"
DETAIL_PATH = REPORT_DIR / "business_detector_v5_categorical_ablation_alerts.csv"
SUMMARY_PATH = REPORT_DIR / "business_detector_v5_categorical_ablation_summary.csv"
OVERLAP_PATH = REPORT_DIR / "business_detector_v5_categorical_ablation_overlap.csv"
JSON_PATH = REPORT_DIR / "business_detector_v5_categorical_ablation.json"

VARIANTS = {
    "full_model": list(v5.NUMERIC_FEATURES + v5.CATEGORICAL_FEATURES),
    "no_action": list(v5.NUMERIC_FEATURES + ["method", "resource_type"]),
    "no_method": list(v5.NUMERIC_FEATURES + ["action", "resource_type"]),
    "no_resource_type": list(v5.NUMERIC_FEATURES + ["action", "method"]),
    "behavior_only": list(v5.NUMERIC_FEATURES),
}


def make_ablation_forest(feature_columns: list[str]) -> Pipeline:
    numeric_columns = [
        column for column in v5.NUMERIC_FEATURES if column in feature_columns
    ]
    categorical_columns = [
        column for column in v5.CATEGORICAL_FEATURES if column in feature_columns
    ]

    transformers = []

    if numeric_columns:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("numeric", numeric_pipeline, numeric_columns))

    if categorical_columns:
        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="constant", fill_value="__MISSING__"),
                ),
                (
                    "onehot",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                ),
            ]
        )
        transformers.append(
            ("categorical", categorical_pipeline, categorical_columns)
        )

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )

    detector = IsolationForest(
        n_estimators=v5.N_ESTIMATORS,
        contamination="auto",
        random_state=v5.RANDOM_STATE,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("detector", detector),
        ]
    )


def select_positions(scores: np.ndarray, budget: float) -> tuple[list[int], dict[str, Any]]:
    scores = np.asarray(scores, dtype=float)
    n_rows = len(scores)
    k = min(n_rows, max(1, int(np.floor(n_rows * budget)))) if n_rows else 0
    order = np.argsort(-scores, kind="stable")
    positions = [int(position) for position in order[:k]]

    if k:
        boundary_score = float(scores[positions[-1]])
        boundary_ties = int(np.sum(scores == boundary_score))
    else:
        boundary_score = None
        boundary_ties = 0

    return positions, {
        "selected_count": int(k),
        "evaluation_rows": int(n_rows),
        "selected_rate_pct": float(100 * k / n_rows) if n_rows else 0.0,
        "minimum_selected_score": boundary_score,
        "rows_tied_at_selection_boundary": boundary_ties,
        "top_score_mean": float(np.mean(scores[positions])) if positions else None,
    }


def category_counts(frame: pd.DataFrame, positions: list[int]) -> dict[str, dict[str, int]]:
    selected = frame.iloc[positions]
    output: dict[str, dict[str, int]] = {}
    for column in v5.CATEGORICAL_FEATURES:
        output[column] = {
            str(key): int(value)
            for key, value in selected[column].astype(str).value_counts().items()
        }
    return output


def jaccard(left: set[int], right: set[int]) -> float:
    union = left | right
    return float(100.0 * len(left & right) / len(union)) if union else 0.0


def main() -> None:
    started = time.perf_counter()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print("KBR V5 CATEGORICAL-FEATURE ABLATION")
    print("=" * 76)

    business, dataset_metadata = v5.load_business_dataset()
    features = v5.build_causal_features(business)
    v5.validate_features(features)
    cutoff, cutoff_metadata = v5.get_common_cutoff(features)

    print(f"Business rows: {len(features)}")
    print(f"Dataset SHA-256: {dataset_metadata['dataset_sha256']}")
    print(f"Shared cutoff: {cutoff.isoformat()}")
    print(f"Variants: {', '.join(VARIANTS)}")

    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    overlap_rows: list[dict[str, Any]] = []
    result_metadata: dict[str, Any] = {}

    for gap_minutes in v5.SESSION_GAPS_MINUTES:
        train, evaluation, split_metadata = v5.split_sessions(
            features, gap_minutes, cutoff
        )
        if len(train) < 100 or len(evaluation) < 20:
            raise ValueError(
                f"Insufficient rows for {gap_minutes}-minute sessions: "
                f"train={len(train)}, evaluation={len(evaluation)}"
            )

        print(
            f"\nSession gap {gap_minutes}m: "
            f"train={len(train)} rows, evaluation={len(evaluation)} rows"
        )

        x_train_all = train[v5.NUMERIC_FEATURES + v5.CATEGORICAL_FEATURES]
        x_eval_all = evaluation[v5.NUMERIC_FEATURES + v5.CATEGORICAL_FEATURES]

        variant_scores: dict[str, np.ndarray] = {}
        variant_selected: dict[str, dict[str, list[int]]] = {}
        variant_reports: dict[str, Any] = {}

        for variant_name, feature_columns in VARIANTS.items():
            fit_start = time.perf_counter()
            model = make_ablation_forest(feature_columns)
            model.fit(train[feature_columns])
            train_scores = -model.decision_function(train[feature_columns])
            eval_scores = -model.decision_function(evaluation[feature_columns])
            elapsed = time.perf_counter() - fit_start

            variant_scores[variant_name] = eval_scores
            variant_selected[variant_name] = {}
            variant_reports[variant_name] = {
                "features": feature_columns,
                "fit_and_score_seconds": float(elapsed),
                "training_score_distribution": v5.score_distribution(train_scores),
                "evaluation_score_distribution": v5.score_distribution(eval_scores),
                "budgets": {},
            }

            print(
                f"  {variant_name}: {len(feature_columns)} features, "
                f"{elapsed:.2f}s"
            )

            for budget in v5.ALERT_BUDGETS:
                positions, selection_metadata = select_positions(eval_scores, budget)
                budget_key = f"{int(budget * 100)}%"
                variant_selected[variant_name][budget_key] = positions
                counts = category_counts(evaluation, positions)

                row = {
                    "session_gap_minutes": gap_minutes,
                    "variant": variant_name,
                    "budget_pct": int(budget * 100),
                    **selection_metadata,
                    "selected_category_counts": json.dumps(
                        counts, ensure_ascii=False, sort_keys=True
                    ),
                }
                summary_rows.append(row)

                variant_reports[variant_name]["budgets"][budget_key] = {
                    **selection_metadata,
                    "selected_category_counts": counts,
                }

                for rank, position in enumerate(positions, start=1):
                    event = evaluation.iloc[position]
                    detail_rows.append(
                        {
                            "session_gap_minutes": gap_minutes,
                            "variant": variant_name,
                            "budget_pct": int(budget * 100),
                            "rank": rank,
                            "evaluation_position": position,
                            "timestamp": event["_timestamp"].isoformat(),
                            "action": str(event.get("action", "__MISSING__")),
                            "method": str(event.get("method", "__MISSING__")),
                            "resource_type": str(
                                event.get("resource_type", "__MISSING__")
                            ),
                            "score": float(eval_scores[position]),
                            "gap_log_seconds": float(event["gap_log_seconds"]),
                            "events_previous_5m": int(event["events_previous_5m"]),
                            "events_previous_1h": int(event["events_previous_1h"]),
                        }
                    )

        # Compare each ablation to the full model using identical evaluation rows.
        for budget in v5.ALERT_BUDGETS:
            budget_key = f"{int(budget * 100)}%"
            full_set = set(variant_selected["full_model"][budget_key])

            for variant_name in VARIANTS:
                variant_set = set(variant_selected[variant_name][budget_key])
                overlap_rows.append(
                    {
                        "session_gap_minutes": gap_minutes,
                        "budget_pct": int(budget * 100),
                        "reference_variant": "full_model",
                        "comparison_variant": variant_name,
                        "full_model_alerts": len(full_set),
                        "comparison_alerts": len(variant_set),
                        "overlap_count": len(full_set & variant_set),
                        "union_count": len(full_set | variant_set),
                        "jaccard_pct": jaccard(full_set, variant_set),
                        "full_only_count": len(full_set - variant_set),
                        "comparison_only_count": len(variant_set - full_set),
                    }
                )

        result_metadata[str(gap_minutes)] = {
            "split": split_metadata,
            "variants": variant_reports,
        }

    detail_df = pd.DataFrame(detail_rows)
    summary_df = pd.DataFrame(summary_rows)
    overlap_df = pd.DataFrame(overlap_rows)

    detail_df.to_csv(DETAIL_PATH, index=False, encoding="utf-8-sig")
    summary_df.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
    overlap_df.to_csv(OVERLAP_PATH, index=False, encoding="utf-8-sig")

    report = {
        "experiment": "V5 categorical-feature ablation",
        "dataset": dataset_metadata,
        "common_cutoff": cutoff_metadata,
        "methodology": {
            "session_gaps_minutes": v5.SESSION_GAPS_MINUTES,
            "alert_budgets": [int(x * 100) for x in v5.ALERT_BUDGETS],
            "random_state": v5.RANDOM_STATE,
            "n_estimators": v5.N_ESTIMATORS,
            "variants": VARIANTS,
            "same_split_per_gap": True,
            "same_rows_for_all_variants_within_gap": True,
            "production_models_modified": False,
            "existing_risk_report_modified": False,
            "labels_available": False,
            "accuracy_metrics_available": False,
            "interpretation": (
                "This experiment measures how feature removal changes rankings "
                "and category concentration. Without verified anomaly labels, "
                "it does not establish accuracy or malicious activity."
            ),
        },
        "results_by_session_gap_minutes": result_metadata,
        "runtime_seconds": float(time.perf_counter() - started),
    }

    JSON_PATH.write_text(
        json.dumps(v5.json_safe(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 76)
    print("ABLATION COMPLETED")
    print("=" * 76)
    print(f"Alerts CSV:   {DETAIL_PATH}")
    print(f"Summary CSV:  {SUMMARY_PATH}")
    print(f"Overlap CSV:  {OVERLAP_PATH}")
    print(f"JSON report:  {JSON_PATH}")
    print("Production models modified: False")
    print("Existing risk report modified: False")


if __name__ == "__main__":
    main()
