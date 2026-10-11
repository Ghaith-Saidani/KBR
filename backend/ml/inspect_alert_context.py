"""
Inspect the raw business-event context around the alerts selected by benchmark V5.

Run from the KBR project root:
    python -m backend.ml.inspect_alert_context

Inputs:
    data/processed/user_activities.csv
    data/reports/business_detector_alert_diagnostics.csv

Output:
    data/reports/business_detector_alert_context.csv

This is diagnostic only. It does not modify production models or risk reports.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
DIAGNOSTICS_PATH = ROOT / "data" / "reports" / "business_detector_alert_diagnostics.csv"
OUTPUT_PATH = ROOT / "data" / "reports" / "business_detector_alert_context.csv"

HTTP_RESOURCE_TYPE = "http_request"
DEFAULT_ALERT_BUDGET = "5%"
DEFAULT_WINDOW_ROWS = 10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_existing_column(frame: pd.DataFrame, candidates: list[str], purpose: str) -> str:
    for name in candidates:
        if name in frame.columns:
            return name
    raise ValueError(
        f"Could not find the {purpose} column. Tried {candidates}. "
        f"Available columns: {list(frame.columns)}"
    )


def normalize_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().fillna("")


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    if not DIAGNOSTICS_PATH.exists():
        raise FileNotFoundError(
            f"Diagnostics CSV not found: {DIAGNOSTICS_PATH}\n"
            "Run the V5 alert diagnostics script first."
        )

    raw = pd.read_csv(DATASET_PATH, low_memory=False)
    alerts = pd.read_csv(DIAGNOSTICS_PATH, low_memory=False)

    timestamp_col = first_existing_column(
        raw, ["created_at", "timestamp", "occurred_at", "event_time"], "timestamp"
    )
    alert_timestamp_col = first_existing_column(
        alerts, ["timestamp", "created_at", "event_timestamp"], "alert timestamp"
    )
    action_col = first_existing_column(raw, ["action", "event_type", "activity"], "action")
    resource_col = first_existing_column(
        raw, ["resource_type", "resource", "category"], "resource type"
    )
    method_col = next((c for c in ["method", "http_method"] if c in raw.columns), None)

    raw["_context_timestamp"] = pd.to_datetime(
        raw[timestamp_col], errors="coerce", format="mixed", utc=True
    )
    raw = raw.loc[raw["_context_timestamp"].notna()].copy()

    resource_types = normalize_text(raw[resource_col])
    http_mask = resource_types.eq(HTTP_RESOURCE_TYPE)
    business = raw.loc[~http_mask].copy()
    business = business.sort_values("_context_timestamp", kind="stable").reset_index(drop=True)

    # Canonical fields are used only for matching; original source columns are retained.
    business["_match_action"] = normalize_text(business[action_col])
    business["_match_resource"] = normalize_text(business[resource_col])
    business["_match_method"] = (
        normalize_text(business[method_col]) if method_col else ""
    )

    alerts["_alert_timestamp"] = pd.to_datetime(
        alerts[alert_timestamp_col], errors="coerce", format="mixed", utc=True
    )
    alerts = alerts.loc[alerts["_alert_timestamp"].notna()].copy()

    if "alert_budget" in alerts.columns:
        selected = alerts.loc[
            alerts["alert_budget"].astype(str).str.strip().eq(DEFAULT_ALERT_BUDGET)
        ].copy()
    else:
        selected = alerts.copy()

    if selected.empty:
        raise ValueError(
            f"No alert rows found for alert_budget={DEFAULT_ALERT_BUDGET!r}. "
            "Check the diagnostics CSV's alert_budget values."
        )

    # Deduplicate the same event selected by multiple detectors/session settings.
    # Preserve the detector names and benchmark settings that selected each event.
    key_cols = ["_alert_timestamp"]
    for col in ["action", "method", "resource_type"]:
        if col in selected.columns:
            key_cols.append(col)

    selected["_anchor_action"] = (
        normalize_text(selected["action"]) if "action" in selected.columns else ""
    )
    selected["_anchor_resource"] = (
        normalize_text(selected["resource_type"])
        if "resource_type" in selected.columns else ""
    )
    selected["_anchor_method"] = (
        normalize_text(selected["method"]) if "method" in selected.columns else ""
    )

    anchor_keys = [
        "_alert_timestamp", "_anchor_action", "_anchor_resource", "_anchor_method"
    ]
    aggregation = {}
    for col in ["detector", "session_gap_minutes", "alert_budget", "rank_within_budget"]:
        if col in selected.columns:
            aggregation[col] = lambda s: ";".join(
                sorted({str(v) for v in s.dropna().tolist()})
            )

    anchors = (
        selected.groupby(anchor_keys, dropna=False, sort=True)
        .agg(aggregation)
        .reset_index()
        .rename(columns={"_alert_timestamp": "anchor_timestamp"})
    )
    anchors["anchor_id"] = [f"A{i:04d}" for i in range(1, len(anchors) + 1)]

    # Map each alert anchor to its matching business event. Timestamp plus action,
    # resource type, and method reduces accidental matches on timestamp alone.
    raw_keys = business[
        ["_context_timestamp", "_match_action", "_match_resource", "_match_method"]
    ].copy()
    raw_keys["_source_row_index"] = business.index

    records: list[dict] = []
    window = DEFAULT_WINDOW_ROWS
    for _, anchor in anchors.iterrows():
        match = (
            business["_context_timestamp"].eq(anchor["anchor_timestamp"])
            & business["_match_action"].eq(anchor["_anchor_action"])
            & business["_match_resource"].eq(anchor["_anchor_resource"])
        )
        if method_col:
            match &= business["_match_method"].eq(anchor["_anchor_method"])

        match_indices = business.index[match].tolist()
        if not match_indices:
            # Fall back to exact timestamp if a field's representation differs.
            match_indices = business.index[
                business["_context_timestamp"].eq(anchor["anchor_timestamp"])
            ].tolist()

        if not match_indices:
            records.append({
                "anchor_id": anchor["anchor_id"],
                "anchor_timestamp": anchor["anchor_timestamp"],
                "context_status": "anchor_not_found",
                "event_offset_from_anchor": 0,
            })
            continue

        # If duplicate timestamps exist, include the context around each match.
        for matched_index in match_indices:
            start = max(0, matched_index - window)
            end = min(len(business), matched_index + window + 1)
            for event_index in range(start, end):
                event = business.iloc[event_index]
                event_time = event["_context_timestamp"]
                record = {
                    "anchor_id": anchor["anchor_id"],
                    "anchor_timestamp": anchor["anchor_timestamp"],
                    "context_status": "matched",
                    "anchor_event_found": True,
                    "event_offset_from_anchor": int(event_index - matched_index),
                    "event_timestamp": event_time,
                    "seconds_from_anchor": (
                        event_time - anchor["anchor_timestamp"]
                    ).total_seconds(),
                    "is_anchor_event": event_index == matched_index,
                    "anchor_action": anchor["_anchor_action"],
                    "anchor_resource_type": anchor["_anchor_resource"],
                    "anchor_method": anchor["_anchor_method"],
                }
                for col in ["detector", "session_gap_minutes", "alert_budget", "rank_within_budget"]:
                    if col in anchors.columns:
                        record[f"selected_{col}"] = anchor[col]
                for col in raw.columns:
                    if col != "_context_timestamp" and not col.startswith("_match_"):
                        record[f"source_{col}"] = event[col]
                records.append(record)

    context = pd.DataFrame(records)
    if not context.empty:
        sort_cols = [
            c for c in ["anchor_timestamp", "anchor_id", "event_offset_from_anchor"]
            if c in context.columns
        ]
        context = context.sort_values(sort_cols, kind="stable")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    context.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    matched_anchors = (
        int(context.loc[context["context_status"].eq("matched"), "anchor_id"].nunique())
        if not context.empty and "context_status" in context.columns else 0
    )
    print("=" * 72)
    print("KBR V5 ALERT CONTEXT INSPECTION")
    print("=" * 72)
    print(f"Dataset rows loaded: {len(raw)}")
    print(f"Business events used: {len(business)}")
    print(f"HTTP events excluded: {int(http_mask.sum())}")
    print(f"Alert rows at {DEFAULT_ALERT_BUDGET}: {len(selected)}")
    print(f"Unique alert anchors: {len(anchors)}")
    print(f"Anchors with matching source events: {matched_anchors}")
    print(f"Context window: {window} events before and after each anchor")
    print(f"Dataset SHA-256: {sha256_file(DATASET_PATH)}")
    print(f"Output: {OUTPUT_PATH.relative_to(ROOT)}")
    print("Production models modified: False")
    print("Existing risk report modified: False")


if __name__ == "__main__":
    main()
