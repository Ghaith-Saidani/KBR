"""
KBR V5 alert diagnostics.

Reads:
  data/processed/user_activities.csv
  data/reports/business_detector_benchmark_v5.json

Writes:
  data/reports/business_detector_alert_diagnostics.csv

This script does not train, save, or modify production models or risk reports.
Run from the repository root:
  python -m backend.ml.diagnose_business_detector_alerts
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
REPORT_PATH = ROOT / "data" / "reports" / "business_detector_benchmark_v5.json"
OUTPUT_PATH = ROOT / "data" / "reports" / "business_detector_alert_diagnostics.csv"

HTTP_RESOURCE_TYPE = "http_request"
TIMESTAMP_CANDIDATES = ("timestamp", "created_at", "event_timestamp", "datetime", "time")
CATEGORICAL_FIELDS = ("action", "method", "resource_type")


def find_timestamp_column(frame: pd.DataFrame) -> str:
    for column in TIMESTAMP_CANDIDATES:
        if column in frame.columns:
            return column
    raise ValueError(
        "Could not find a timestamp column. Tried: "
        + ", ".join(TIMESTAMP_CANDIDATES)
        + f". Available columns: {', '.join(map(str, frame.columns))}"
    )


def load_business_events() -> tuple[pd.DataFrame, str]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    frame = pd.read_csv(DATASET_PATH, low_memory=False)
    timestamp_column = find_timestamp_column(frame)

    if "resource_type" not in frame.columns:
        raise ValueError("Dataset is missing required column 'resource_type'.")

    frame["_timestamp"] = pd.to_datetime(
        frame[timestamp_column],
        errors="coerce",
        format="mixed",
        utc=True,
    )
    frame = frame.dropna(subset=["_timestamp"]).copy()

    resource_types = (
        frame["resource_type"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    http_mask = resource_types.eq(HTTP_RESOURCE_TYPE).fillna(False)
    frame = frame.loc[~http_mask].copy()

    for column in CATEGORICAL_FIELDS:
        if column not in frame.columns:
            frame[column] = "__MISSING__"
        frame[column] = (
            frame[column]
            .astype("string")
            .fillna("__MISSING__")
            .astype(str)
        )

    frame = frame.sort_values("_timestamp", kind="stable").reset_index(drop=True)

    # Causal features: the current event is not included in rolling counts.
    gaps = frame["_timestamp"].diff().dt.total_seconds()
    positive_gaps = gaps[gaps > 0]
    fallback_gap = float(positive_gaps.median()) if not positive_gaps.empty else 60.0
    frame["gap_seconds"] = gaps.fillna(fallback_gap).clip(lower=0.001)

    previous_5m: deque[pd.Timestamp] = deque()
    previous_1h: deque[pd.Timestamp] = deque()
    counts_5m: list[int] = []
    counts_1h: list[int] = []

    for timestamp in frame["_timestamp"]:
        while previous_5m and (timestamp - previous_5m[0]).total_seconds() >= 300:
            previous_5m.popleft()
        while previous_1h and (timestamp - previous_1h[0]).total_seconds() >= 3600:
            previous_1h.popleft()

        counts_5m.append(len(previous_5m))
        counts_1h.append(len(previous_1h))
        previous_5m.append(timestamp)
        previous_1h.append(timestamp)

    frame["events_previous_5m"] = counts_5m
    frame["events_previous_1h"] = counts_1h
    frame["gap_log_seconds"] = np.log1p(frame["gap_seconds"])

    frame["hour_utc"] = frame["_timestamp"].dt.hour
    frame["weekday_utc"] = frame["_timestamp"].dt.dayofweek

    return frame, timestamp_column


def normalize_event_value(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "__MISSING__"
    return str(value)


def event_key(timestamp: Any, action: Any, method: Any, resource_type: Any) -> tuple[str, str, str, str]:
    parsed = pd.to_datetime(timestamp, utc=True, errors="coerce")
    timestamp_key = parsed.isoformat() if not pd.isna(parsed) else str(timestamp)
    return (
        timestamp_key,
        normalize_event_value(action),
        normalize_event_value(method),
        normalize_event_value(resource_type),
    )


def extract_selected_alerts(report: dict[str, Any]) -> pd.DataFrame:
    output: list[dict[str, Any]] = []
    results = report.get("results_by_session_gap_minutes", {})

    for gap, gap_report in results.items():
        split = gap_report.get("split", {})
        cutoff = split.get("common_cutoff") or split.get("evaluation_start")

        for detector_name, detector_report in gap_report.get("detectors", {}).items():
            budgets = detector_report.get("fixed_alert_budgets", {})

            for budget, budget_report in budgets.items():
                alerts = budget_report.get("selected_alerts", [])
                # Ranking is based on score descending; the report's selected
                # list may be stored in rank order, so sort explicitly.
                alerts = sorted(
                    alerts,
                    key=lambda row: float(row.get("score", float("-inf"))),
                    reverse=True,
                )

                for rank, alert in enumerate(alerts, start=1):
                    output.append(
                        {
                            "session_gap_minutes": int(gap),
                            "detector": detector_name,
                            "alert_budget": budget,
                            "rank_within_budget": rank,
                            "timestamp": alert.get("timestamp"),
                            "action": normalize_event_value(alert.get("action")),
                            "method": normalize_event_value(alert.get("method")),
                            "resource_type": normalize_event_value(alert.get("resource_type")),
                            "detector_score": alert.get("score"),
                            "evaluation_cutoff_utc": cutoff,
                        }
                    )

    if not output:
        raise ValueError(
            "No selected_alerts found in the report. Confirm that this is the latest "
            "V5 report and that fixed_alert_budgets contain selected_alerts."
        )

    return pd.DataFrame(output)


def main() -> None:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"V5 report not found: {REPORT_PATH}")

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    events, original_timestamp_column = load_business_events()
    alerts = extract_selected_alerts(report)

    events["_event_key"] = [
        event_key(row["_timestamp"], row["action"], row["method"], row["resource_type"])
        for _, row in events.iterrows()
    ]
    alerts["_event_key"] = [
        event_key(row["timestamp"], row["action"], row["method"], row["resource_type"])
        for _, row in alerts.iterrows()
    ]

    # Compare detectors at the same session gap and alert budget.
    selected_by_group: dict[tuple[int, str], dict[str, set[tuple[str, str, str, str]]]] = {}
    for _, selected in alerts.iterrows():
        group_key = (int(selected["session_gap_minutes"]), str(selected["alert_budget"]))
        selected_by_group.setdefault(group_key, {}).setdefault(str(selected["detector"]), set()).add(
            selected["_event_key"]
        )

    # The report records only selected events, so use a left merge from alerts.
    # If the raw log contains identical composite keys, keep the first matching
    # event and explicitly mark ambiguity rather than multiplying alert rows.
    event_lookup: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    key_counts = events["_event_key"].value_counts().to_dict()

    for _, row in events.iterrows():
        key = row["_event_key"]
        if key not in event_lookup:
            event_lookup[key] = row.to_dict()

    feature_columns = [
        "_timestamp",
        "gap_seconds",
        "gap_log_seconds",
        "events_previous_5m",
        "events_previous_1h",
        "hour_utc",
        "weekday_utc",
    ]
    # Include common optional identity/context fields when available.
    optional_columns = [
        "user_id", "actor_id", "status_code", "status", "ip_address",
        "endpoint", "path", "request_id", "event_type",
    ]
    context_columns = [column for column in optional_columns if column in events.columns]

    output_rows: list[dict[str, Any]] = []

    for _, alert in alerts.iterrows():
        matched = event_lookup.get(alert["_event_key"])
        row = alert.drop(labels=["_event_key"]).to_dict()

        row["source_match_found"] = matched is not None
        row["source_key_match_count"] = int(key_counts.get(alert["_event_key"], 0))
        row["source_match_ambiguous"] = int(key_counts.get(alert["_event_key"], 0)) > 1

        group_key = (int(alert["session_gap_minutes"]), str(alert["alert_budget"]))
        group_detectors = selected_by_group.get(group_key, {})
        other_detectors = [
            detector_name
            for detector_name, keys in group_detectors.items()
            if detector_name != str(alert["detector"]) and alert["_event_key"] in keys
        ]
        row["selected_by_other_detector_same_budget"] = bool(other_detectors)
        row["other_detector_names_same_budget"] = ";".join(other_detectors)

        if matched is not None:
            for column in feature_columns:
                if column in matched:
                    value = matched[column]
                    row[column.lstrip("_")] = value.isoformat() if isinstance(value, pd.Timestamp) else value
            for column in context_columns:
                row[column] = matched.get(column)

            cutoff_value = alert.get("evaluation_cutoff_utc")
            cutoff = pd.to_datetime(cutoff_value, utc=True, errors="coerce")
            event_time = matched.get("_timestamp")

            # This is a transparent approximation: V5's exact session split can
            # exclude sessions crossing the cutoff. We mark category membership
            # based on rows strictly before the cutoff and label it accordingly.
            if not pd.isna(cutoff):
                train = events.loc[events["_timestamp"] < cutoff]
                row["action_seen_before_cutoff"] = (
                    normalize_event_value(alert["action"]) in set(train["action"].astype(str))
                )
                row["resource_type_seen_before_cutoff"] = (
                    normalize_event_value(alert["resource_type"]) in set(train["resource_type"].astype(str))
                )
                row["method_seen_before_cutoff"] = (
                    normalize_event_value(alert["method"]) in set(train["method"].astype(str))
                )
                row["category_membership_note"] = (
                    "Computed from all business rows before the cutoff; approximate only, "
                    "not the exact session-filtered V5 training set."
                )
            else:
                row["action_seen_before_cutoff"] = None
                row["resource_type_seen_before_cutoff"] = None
                row["method_seen_before_cutoff"] = None
                row["category_membership_note"] = "No cutoff found in report."

            row["gap_seconds_interpretation"] = (
                "Shorter gaps may raise the directional baseline score; inspect with "
                "rolling counts. This is descriptive, not a verdict."
            )
        else:
            row["category_membership_note"] = "Could not join alert to source dataset."

        output_rows.append(row)

    result = pd.DataFrame(output_rows)

    # Put the most useful review fields first while preserving extra context fields.
    preferred = [
        "session_gap_minutes", "detector", "alert_budget", "rank_within_budget",
        "detector_score", "timestamp", "action", "method", "resource_type",
        "source_match_found", "source_key_match_count", "source_match_ambiguous",
        "selected_by_other_detector_same_budget", "other_detector_names_same_budget",
        "gap_seconds", "events_previous_5m", "events_previous_1h",
        "action_seen_before_cutoff", "resource_type_seen_before_cutoff",
        "method_seen_before_cutoff", "evaluation_cutoff_utc",
        "hour_utc", "weekday_utc", "category_membership_note",
    ]
    ordered = [column for column in preferred if column in result.columns]
    ordered += [column for column in result.columns if column not in ordered and column != "_event_key"]
    result = result[ordered]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("=" * 72)
    print("KBR V5 ALERT DIAGNOSTICS COMPLETED")
    print("=" * 72)
    print(f"Dataset: {DATASET_PATH.relative_to(ROOT)}")
    print(f"Source timestamp column: {original_timestamp_column}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"Diagnostic rows: {len(result)}")
    print(f"Matched source events: {int(result['source_match_found'].sum())}/{len(result)}")
    print(f"Ambiguous source matches: {int(result['source_match_ambiguous'].sum())}")
    print(f"Output CSV: {OUTPUT_PATH.relative_to(ROOT)}")
    print("Production models modified: False")
    print("Existing risk report modified: False")
    print("\nReview the CSV in Excel. Start by filtering:")
    print("  1. alert_budget = 5%")
    print("  2. compare detector and session_gap_minutes")
    print("  3. compare overlapping timestamps and rolling counts")
    print("  4. inspect rows where action/resource type was unseen before cutoff")
    print("\nCaution: category membership is approximated using timestamps before the")
    print("cutoff; V5 may exclude crossing sessions from its exact training set.")


if __name__ == "__main__":
    main()
