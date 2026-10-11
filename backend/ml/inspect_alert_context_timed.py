"""
Time-bounded investigation of V5 business-detector alerts.

Run from the KBR project root:
    python -m backend.ml.inspect_alert_context_timed

Inputs:
    data/processed/user_activities.csv
    data/reports/business_detector_alert_diagnostics.csv

Outputs:
    data/reports/business_detector_alert_context_2min.csv
    data/reports/business_detector_alert_context_summary.csv

The script is read-only with respect to production models and risk reports.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path.cwd()
DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
DIAGNOSTICS_PATH = ROOT / "data" / "reports" / "business_detector_alert_diagnostics.csv"
CONTEXT_OUTPUT_PATH = ROOT / "data" / "reports" / "business_detector_alert_context_2min.csv"
SUMMARY_OUTPUT_PATH = ROOT / "data" / "reports" / "business_detector_alert_context_summary.csv"

HTTP_RESOURCE_TYPE = "http_request"
ALERT_BUDGET = "5%"
WINDOW_SECONDS = 120


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_column(frame: pd.DataFrame, candidates: list[str], purpose: str) -> str:
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    raise ValueError(
        f"Missing {purpose} column. Tried {candidates}. "
        f"Available columns: {list(frame.columns)}"
    )


def norm(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().fillna("")


def parse_status(value: Any) -> str:
    """Extract an HTTP status code from common details/metadata representations."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value)

    # Typical stored details: "HTTP 403" or JSON/dict with status_code: 403.
    match = re.search(r"\bHTTP\s+(\d{3})\b", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(
        r"""['"]?status_code['"]?\s*[:=]\s*['"]?(\d{3})""",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)

    # Handle JSON or Python-dict strings without relying on a single encoding.
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
        except (ValueError, SyntaxError, TypeError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict):
            status = parsed.get("status_code", parsed.get("status"))
            if status is not None and str(status).isdigit():
                return str(status)
    return ""


def joined_unique(series: pd.Series) -> str:
    values = sorted({str(value).strip() for value in series.dropna() if str(value).strip()})
    return "; ".join(values)


def value_counts_text(series: pd.Series, limit: int = 8) -> str:
    cleaned = series.astype("string").fillna("").str.strip()
    cleaned = cleaned[cleaned.ne("")]
    if cleaned.empty:
        return ""
    counts = cleaned.value_counts().head(limit)
    return "; ".join(f"{name} ({count})" for name, count in counts.items())


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    if not DIAGNOSTICS_PATH.exists():
        raise FileNotFoundError(
            f"Diagnostics CSV not found: {DIAGNOSTICS_PATH}. "
            "Run backend.ml.diagnose_business_detector_alerts first."
        )

    raw = pd.read_csv(DATASET_PATH, low_memory=False)
    diagnostics = pd.read_csv(DIAGNOSTICS_PATH, low_memory=False)

    timestamp_col = find_column(
        raw, ["created_at", "timestamp", "occurred_at", "event_time"], "source timestamp"
    )
    action_col = find_column(raw, ["action", "event_type", "activity"], "source action")
    resource_col = find_column(
        raw, ["resource_type", "resource", "category"], "source resource type"
    )
    method_col = next((c for c in ["method", "http_method"] if c in raw.columns), None)
    user_col = next((c for c in ["user_id", "actor_id"] if c in raw.columns), None)
    ip_col = next((c for c in ["ip_address", "client_ip", "ip"] if c in raw.columns), None)
    endpoint_col = next((c for c in ["endpoint", "path", "resource_path"] if c in raw.columns), None)
    details_col = next((c for c in ["details", "activity_metadata", "metadata"] if c in raw.columns), None)
    user_agent_col = next((c for c in ["user_agent", "client_user_agent"] if c in raw.columns), None)

    diagnostic_timestamp_col = find_column(
        diagnostics, ["timestamp", "created_at", "event_timestamp"], "alert timestamp"
    )

    raw["_event_timestamp"] = pd.to_datetime(
        raw[timestamp_col], errors="coerce", format="mixed", utc=True
    )
    raw = raw.loc[raw["_event_timestamp"].notna()].copy()
    raw["_norm_action"] = norm(raw[action_col])
    raw["_norm_resource"] = norm(raw[resource_col])
    raw["_norm_method"] = norm(raw[method_col]) if method_col else ""

    # Match the V5 benchmark population: every valid-timestamp row except HTTP requests.
    http_mask = raw["_norm_resource"].eq(HTTP_RESOURCE_TYPE)
    business = raw.loc[~http_mask].copy()
    business = business.sort_values("_event_timestamp", kind="stable").reset_index(drop=True)
    business["_source_row_number"] = range(len(business))

    diagnostics["_alert_timestamp"] = pd.to_datetime(
        diagnostics[diagnostic_timestamp_col], errors="coerce", format="mixed", utc=True
    )
    diagnostics = diagnostics.loc[diagnostics["_alert_timestamp"].notna()].copy()
    if "alert_budget" in diagnostics.columns:
        alerts = diagnostics.loc[
            diagnostics["alert_budget"].astype(str).str.strip().eq(ALERT_BUDGET)
        ].copy()
    else:
        alerts = diagnostics.copy()
    if alerts.empty:
        raise ValueError(
            f"No diagnostics rows found for alert budget {ALERT_BUDGET!r}. "
            f"Available values: {diagnostics.get('alert_budget', pd.Series(dtype=str)).unique().tolist()}"
        )

    alerts["_norm_action"] = norm(alerts["action"]) if "action" in alerts.columns else ""
    alerts["_norm_resource"] = (
        norm(alerts["resource_type"]) if "resource_type" in alerts.columns else ""
    )
    alerts["_norm_method"] = norm(alerts["method"]) if "method" in alerts.columns else ""

    anchor_keys = ["_alert_timestamp", "_norm_action", "_norm_resource", "_norm_method"]
    anchors = (
        alerts.groupby(anchor_keys, dropna=False, sort=True)
        .agg(
            selected_detectors=("detector", joined_unique) if "detector" in alerts.columns else ("_norm_action", "first"),
            selected_gap_settings=("session_gap_minutes", joined_unique) if "session_gap_minutes" in alerts.columns else ("_norm_action", "first"),
            selected_ranks=("rank_within_budget", joined_unique) if "rank_within_budget" in alerts.columns else ("_norm_action", "first"),
            selection_count=("_alert_timestamp", "size"),
        )
        .reset_index()
        .rename(columns={
            "_alert_timestamp": "anchor_timestamp",
            "_norm_action": "anchor_action_normalized",
            "_norm_resource": "anchor_resource_type",
            "_norm_method": "anchor_method",
        })
    )
    anchors["anchor_id"] = [f"T{i:04d}" for i in range(1, len(anchors) + 1)]

    context_records: list[dict[str, Any]] = []
    summary_records: list[dict[str, Any]] = []
    window = pd.Timedelta(seconds=WINDOW_SECONDS)

    for _, anchor in anchors.iterrows():
        # Exact timestamp + normalized action/resource/method matching.
        matches = business.loc[
            business["_event_timestamp"].eq(anchor["anchor_timestamp"])
            & business["_norm_action"].eq(anchor["anchor_action_normalized"])
            & business["_norm_resource"].eq(anchor["anchor_resource_type"])
        ]
        if method_col:
            matches = matches.loc[matches["_norm_method"].eq(anchor["anchor_method"])]

        if matches.empty:
            matches = business.loc[
                business["_event_timestamp"].eq(anchor["anchor_timestamp"])
            ]

        if matches.empty:
            summary_records.append({
                "anchor_id": anchor["anchor_id"],
                "anchor_timestamp": anchor["anchor_timestamp"],
                "anchor_action": anchor["anchor_action_normalized"],
                "anchor_resource_type": anchor["anchor_resource_type"],
                "anchor_method": anchor["anchor_method"],
                "selected_detectors": anchor["selected_detectors"],
                "selected_gap_settings": anchor["selected_gap_settings"],
                "selected_ranks": anchor["selected_ranks"],
                "selection_count": anchor["selection_count"],
                "context_status": "anchor_not_found",
                "context_events_2min": 0,
            })
            continue

        # Usually there is one exact match. Handle duplicate source events safely.
        for _, anchor_event in matches.iterrows():
            anchor_time = anchor_event["_event_timestamp"]
            lower = anchor_time - window
            upper = anchor_time + window
            context_events = business.loc[
                business["_event_timestamp"].between(lower, upper, inclusive="both")
            ].copy()
            context_events["seconds_from_anchor"] = (
                context_events["_event_timestamp"] - anchor_time
            ).dt.total_seconds()

            anchor_user = (
                str(anchor_event[user_col]).strip()
                if user_col and pd.notna(anchor_event[user_col]) else ""
            )
            anchor_ip = (
                str(anchor_event[ip_col]).strip()
                if ip_col and pd.notna(anchor_event[ip_col]) else ""
            )
            context_events["is_anchor_event"] = (
                context_events["_source_row_number"].eq(anchor_event["_source_row_number"])
            )
            context_events["same_user_as_anchor"] = (
                context_events[user_col].astype("string").fillna("").str.strip().eq(anchor_user)
                if user_col and anchor_user else False
            )
            context_events["same_ip_as_anchor"] = (
                context_events[ip_col].astype("string").fillna("").str.strip().eq(anchor_ip)
                if ip_col and anchor_ip else False
            )
            context_events["relative_position"] = context_events["seconds_from_anchor"].map(
                lambda value: "before" if value < 0 else ("after" if value > 0 else "same_time")
            )

            # Include only useful original fields plus explicit context/matching metadata.
            for _, event in context_events.iterrows():
                record: dict[str, Any] = {
                    "anchor_id": anchor["anchor_id"],
                    "anchor_timestamp": anchor_time,
                    "context_window_seconds": WINDOW_SECONDS,
                    "event_timestamp": event["_event_timestamp"],
                    "seconds_from_anchor": event["seconds_from_anchor"],
                    "relative_position": event["relative_position"],
                    "is_anchor_event": bool(event["is_anchor_event"]),
                    "same_user_as_anchor": bool(event["same_user_as_anchor"]),
                    "same_ip_as_anchor": bool(event["same_ip_as_anchor"]),
                    "anchor_action": anchor["anchor_action_normalized"],
                    "anchor_resource_type": anchor["anchor_resource_type"],
                    "anchor_method": anchor["anchor_method"],
                    "selected_detectors": anchor["selected_detectors"],
                    "selected_gap_settings": anchor["selected_gap_settings"],
                    "selected_ranks": anchor["selected_ranks"],
                    "source_row_number": int(event["_source_row_number"]),
                }
                for col in raw.columns:
                    if col.startswith("_"):
                        continue
                    record[f"source_{col}"] = event[col]
                record["parsed_status_code"] = (
                    parse_status(event[details_col]) if details_col else ""
                )
                context_records.append(record)

            status_counts = (
                context_events[details_col].map(parse_status).replace("", pd.NA).dropna().value_counts()
                if details_col else pd.Series(dtype=int)
            )
            status_summary = "; ".join(
                f"{status} ({count})" for status, count in status_counts.items()
            )
            same_user_events = int(context_events["same_user_as_anchor"].sum())
            same_ip_events = int(context_events["same_ip_as_anchor"].sum())
            before_count = int((context_events["seconds_from_anchor"] < 0).sum())
            after_count = int((context_events["seconds_from_anchor"] > 0).sum())

            summary: dict[str, Any] = {
                "anchor_id": anchor["anchor_id"],
                "anchor_timestamp": anchor_time,
                "selected_detectors": anchor["selected_detectors"],
                "selected_gap_settings": anchor["selected_gap_settings"],
                "selected_ranks": anchor["selected_ranks"],
                "selection_count": int(anchor["selection_count"]),
                "anchor_action": anchor["anchor_action_normalized"],
                "anchor_resource_type": anchor["anchor_resource_type"],
                "anchor_method": anchor["anchor_method"],
                "anchor_user_id": anchor_user,
                "anchor_ip_address": anchor_ip,
                "anchor_endpoint": (
                    str(anchor_event[endpoint_col])
                    if endpoint_col and pd.notna(anchor_event[endpoint_col]) else ""
                ),
                "anchor_user_agent": (
                    str(anchor_event[user_agent_col])
                    if user_agent_col and pd.notna(anchor_event[user_agent_col]) else ""
                ),
                "context_status": "matched",
                "context_events_2min": len(context_events),
                "events_before_anchor": before_count,
                "events_after_anchor": after_count,
                "events_same_user": same_user_events,
                "events_same_ip": same_ip_events,
                "distinct_user_ids": (
                    int(context_events[user_col].dropna().astype(str).nunique()) if user_col else 0
                ),
                "distinct_ip_addresses": (
                    int(context_events[ip_col].dropna().astype(str).nunique()) if ip_col else 0
                ),
                "top_actions": value_counts_text(context_events[action_col]),
                "resource_type_counts": value_counts_text(context_events[resource_col]),
                "response_status_counts": status_summary,
                "dataset_sha256": sha256_file(DATASET_PATH),
            }
            summary_records.append(summary)

    context_df = pd.DataFrame(context_records)
    summary_df = pd.DataFrame(summary_records)

    if not context_df.empty:
        context_df = context_df.sort_values(
            ["anchor_timestamp", "anchor_id", "seconds_from_anchor"], kind="stable"
        )
    if not summary_df.empty:
        summary_df = summary_df.sort_values(["anchor_timestamp", "anchor_id"], kind="stable")

    CONTEXT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    context_df.to_csv(CONTEXT_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    summary_df.to_csv(SUMMARY_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    matched = int(summary_df["context_status"].eq("matched").sum()) if not summary_df.empty else 0
    print("=" * 72)
    print("KBR V5 TIME-BOUNDED ALERT CONTEXT")
    print("=" * 72)
    print(f"Original rows loaded: {len(raw)}")
    print(f"Valid timestamp rows: {int(raw['_event_timestamp'].notna().sum())}")
    print(f"HTTP rows excluded: {int(http_mask.sum())}")
    print(f"Business events used: {len(business)}")
    print(f"5% alert diagnostic rows: {len(alerts)}")
    print(f"Unique alert anchors: {len(anchors)}")
    print(f"Anchors matched: {matched}/{len(anchors)}")
    print(f"Time window: +/- {WINDOW_SECONDS} seconds")
    print(f"Context rows written: {len(context_df)}")
    print(f"Context output: {CONTEXT_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Summary output: {SUMMARY_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Dataset SHA-256: {sha256_file(DATASET_PATH)}")
    print("Production models modified: False")
    print("Existing risk report modified: False")


if __name__ == "__main__":
    main()
