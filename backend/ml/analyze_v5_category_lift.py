"""
Measure which business-event categories are overrepresented in V5 selected alerts.

Run from the KBR project root:
    python -m backend.ml.analyze_v5_category_lift

Inputs:
    data/reports/business_detector_benchmark_v5.json
    data/processed/user_activities.csv
    data/reports/business_detector_v5_alert_stability.csv

Outputs:
    data/reports/business_detector_v5_category_lift.csv
    data/reports/business_detector_v5_category_lift_summary.csv

This is a descriptive diagnostic. Category lift is not a measure of model accuracy.
No model training or production artifacts are changed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
REPORT_PATH = ROOT / "data" / "reports" / "business_detector_benchmark_v5.json"
DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
ALERTS_PATH = ROOT / "data" / "reports" / "business_detector_v5_alert_stability.csv"
DETAIL_OUTPUT = ROOT / "data" / "reports" / "business_detector_v5_category_lift.csv"
SUMMARY_OUTPUT = ROOT / "data" / "reports" / "business_detector_v5_category_lift_summary.csv"

DETECTORS = ["isolation_forest", "directional_robust_baseline"]
GAPS = [1, 5]
BUDGETS = ["1%", "2%", "5%"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().fillna("(missing)")


def get_cutoff(report: dict) -> pd.Timestamp:
    method = report.get("evaluation_method", {})
    common = method.get("common_chronological_cutoff", {})
    value = common.get("common_cutoff")
    if not value:
        raise ValueError(
            "Could not find evaluation_method.common_chronological_cutoff.common_cutoff "
            "in the V5 benchmark report."
        )
    cutoff = pd.to_datetime(value, errors="coerce", format="mixed", utc=True)
    if pd.isna(cutoff):
        raise ValueError(f"Invalid benchmark cutoff: {value!r}")
    return cutoff


def main() -> None:
    for path in [REPORT_PATH, DATASET_PATH, ALERTS_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    cutoff = get_cutoff(report)
    raw = pd.read_csv(DATASET_PATH, low_memory=False)
    alerts = pd.read_csv(ALERTS_PATH, low_memory=False)

    timestamp_col = next(
        (c for c in ["created_at", "timestamp", "occurred_at", "event_time"] if c in raw.columns),
        None,
    )
    action_col = next((c for c in ["action", "event_type", "activity"] if c in raw.columns), None)
    resource_col = next((c for c in ["resource_type", "resource", "category"] if c in raw.columns), None)
    if not timestamp_col or not action_col or not resource_col:
        raise ValueError("Dataset needs timestamp, action, and resource_type columns.")

    raw["_ts"] = pd.to_datetime(raw[timestamp_col], errors="coerce", format="mixed", utc=True)
    raw = raw.loc[raw["_ts"].notna()].copy()
    raw["_resource_norm"] = normalize(raw[resource_col])
    raw["_action_norm"] = normalize(raw[action_col])

    # Business-only evaluation rows after the benchmark's shared cutoff.
    business = raw.loc[
        ~raw["_resource_norm"].eq("http_request")
        & raw["_ts"].gt(cutoff)
    ].copy()
    if business.empty:
        raise ValueError("No business rows found after the shared benchmark cutoff.")

    alerts["timestamp_utc"] = pd.to_datetime(
        alerts["timestamp_utc"], errors="coerce", format="mixed", utc=True
    )
    alerts = alerts.loc[alerts["timestamp_utc"].notna()].copy()
    alerts["resource_type_norm"] = normalize(alerts["resource_type"])
    alerts["action_norm"] = normalize(alerts["action"])

    detail_rows = []
    for gap in GAPS:
        population = business.copy()
        population_count = len(population)

        for dimension in ["resource_type", "action"]:
            pop_col = "_resource_norm" if dimension == "resource_type" else "_action_norm"
            population_counts = population[pop_col].value_counts(dropna=False)
            population_share = population_counts / population_count

            for detector in DETECTORS:
                for budget in BUDGETS:
                    selected = alerts.loc[
                        pd.to_numeric(alerts["session_gap_minutes"], errors="coerce").eq(gap)
                        & alerts["detector"].astype(str).eq(detector)
                        & alerts["alert_budget"].astype(str).eq(budget)
                    ].copy()
                    selected_count = len(selected)
                    if selected_count == 0:
                        continue

                    selected_col = (
                        "resource_type_norm" if dimension == "resource_type" else "action_norm"
                    )
                    selected_counts = selected[selected_col].value_counts(dropna=False)
                    selected_share = selected_counts / selected_count
                    categories = sorted(set(population_share.index) | set(selected_share.index))

                    for category in categories:
                        pop_n = int(population_counts.get(category, 0))
                        selected_n = int(selected_counts.get(category, 0))
                        pop_pct = float(population_share.get(category, 0.0) * 100)
                        selected_pct = float(selected_share.get(category, 0.0) * 100)
                        lift = (
                            selected_pct / pop_pct
                            if pop_pct > 0
                            else (None if selected_pct == 0 else float("inf"))
                        )
                        detail_rows.append({
                            "session_gap_minutes": gap,
                            "detector": detector,
                            "alert_budget": budget,
                            "dimension": dimension,
                            "category": category,
                            "evaluation_population_rows": population_count,
                            "selected_alert_rows": selected_count,
                            "population_category_count": pop_n,
                            "selected_category_count": selected_n,
                            "population_share_pct": round(pop_pct, 4),
                            "selected_alert_share_pct": round(selected_pct, 4),
                            "selection_lift": round(lift, 4) if lift is not None and pd.notna(lift) else "",
                            "interpretation": "descriptive category representation; not accuracy",
                        })

    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        raise ValueError("No category comparisons could be calculated.")

    # Keep only categories represented in at least one selected alert for concise summary.
    summary = detail.loc[detail["selected_category_count"].gt(0)].copy()
    summary = summary.sort_values(
        ["session_gap_minutes", "detector", "alert_budget", "dimension",
         "selected_alert_share_pct"],
        ascending=[True, True, True, True, False],
        kind="stable",
    )

    DETAIL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(DETAIL_OUTPUT, index=False, encoding="utf-8-sig")
    summary.to_csv(SUMMARY_OUTPUT, index=False, encoding="utf-8-sig")

    print("=" * 72)
    print("KBR V5 CATEGORY REPRESENTATION / LIFT")
    print("=" * 72)
    print(f"Shared cutoff UTC: {cutoff.isoformat()}")
    print(f"Business evaluation population rows: {len(business)}")
    print(f"Category detail rows: {len(detail)}")
    print(f"Summary rows with selected alerts: {len(summary)}")
    print(f"Detail output: {DETAIL_OUTPUT.relative_to(ROOT)}")
    print(f"Summary output: {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"Benchmark SHA-256: {sha256_file(REPORT_PATH)}")
    print(f"Dataset SHA-256: {sha256_file(DATASET_PATH)}")
    print("Accuracy inferred: False")
    print("Models retrained: False")
    print("Production models modified: False")
    print("Existing risk report modified: False")
    print()
    key = summary.loc[
        summary["alert_budget"].eq("5%")
        & summary["dimension"].eq("resource_type"),
        ["session_gap_minutes", "detector", "category",
         "population_share_pct", "selected_alert_share_pct", "selection_lift"]
    ]
    print("5% alert budget — resource type representation:")
    if key.empty:
        print("No matching rows.")
    else:
        print(key.to_string(index=False))


if __name__ == "__main__":
    main()
