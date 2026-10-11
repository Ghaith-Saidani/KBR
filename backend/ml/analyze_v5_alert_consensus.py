"""
Build an event-level consensus/disagreement report from the V5 stability output.

Run from the KBR project root:
    python -m backend.ml.analyze_v5_alert_consensus

Input:
    data/reports/business_detector_v5_alert_stability.csv

Outputs:
    data/reports/business_detector_v5_alert_consensus.csv
    data/reports/business_detector_v5_alert_consensus_summary.csv

This does not label events as malicious/benign and does not modify models or risk reports.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
INPUT_PATH = ROOT / "data" / "reports" / "business_detector_v5_alert_stability.csv"
CONSENSUS_PATH = ROOT / "data" / "reports" / "business_detector_v5_alert_consensus.csv"
SUMMARY_PATH = ROOT / "data" / "reports" / "business_detector_v5_alert_consensus_summary.csv"

EXPECTED_DETECTORS = ["isolation_forest", "directional_robust_baseline"]
EXPECTED_GAPS = [1, 5]
EXPECTED_BUDGETS = ["1%", "2%", "5%"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm(value: object) -> str:
    return "" if pd.isna(value) else str(value).strip().lower()


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing input: {INPUT_PATH}\n"
            "Run backend.ml.analyze_v5_alert_stability first."
        )

    data = pd.read_csv(INPUT_PATH, low_memory=False)
    required = {
        "session_gap_minutes", "detector", "alert_budget", "rank",
        "timestamp_utc", "action", "method", "resource_type",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Input is missing columns: {sorted(missing)}")

    data["timestamp_utc"] = pd.to_datetime(
        data["timestamp_utc"], errors="coerce", format="mixed", utc=True
    )
    data = data.loc[data["timestamp_utc"].notna()].copy()
    data["session_gap_minutes"] = pd.to_numeric(
        data["session_gap_minutes"], errors="coerce"
    ).astype("Int64")
    for col in ["detector", "alert_budget", "action", "method", "resource_type"]:
        data[col] = data[col].map(norm)

    key_cols = ["timestamp_utc", "action", "method", "resource_type"]
    data["event_key"] = data[key_cols].astype(str).agg("|".join, axis=1)

    # Each selected event appears once per detector/gap/budget combination.
    data = data.drop_duplicates(
        subset=["event_key", "detector", "session_gap_minutes", "alert_budget"],
        keep="first",
    )

    # Build one row per event with all selection combinations as explicit columns.
    records = []
    for event_key, group in data.groupby("event_key", sort=False):
        first = group.iloc[0]
        record = {
            "event_key": event_key,
            "timestamp_utc": first["timestamp_utc"],
            "action": first["action"],
            "method": first["method"],
            "resource_type": first["resource_type"],
            "user_id": "; ".join(sorted({
                str(v).strip() for v in group["user_id"].dropna() if str(v).strip()
            })) if "user_id" in group.columns else "",
            "ip_address": "; ".join(sorted({
                str(v).strip() for v in group["ip_address"].dropna() if str(v).strip()
            })) if "ip_address" in group.columns else "",
            "endpoint": "; ".join(sorted({
                str(v).strip() for v in group["endpoint"].dropna() if str(v).strip()
            })) if "endpoint" in group.columns else "",
            "selected_in_combinations": len(group),
        }

        for detector in EXPECTED_DETECTORS:
            for gap in EXPECTED_GAPS:
                for budget in EXPECTED_BUDGETS:
                    subset = group.loc[
                        group["detector"].eq(detector)
                        & group["session_gap_minutes"].eq(gap)
                        & group["alert_budget"].eq(budget)
                    ]
                    prefix = f"{detector}_gap{gap}_{budget.replace('%', 'pct')}"
                    record[f"{prefix}_selected"] = not subset.empty
                    record[f"{prefix}_rank"] = (
                        int(subset.iloc[0]["rank"]) if not subset.empty else ""
                    )
                    record[f"{prefix}_score"] = (
                        subset.iloc[0]["score"] if not subset.empty else ""
                    )

        record["selected_by_isolation_forest_5pct_any_gap"] = any(
            not group.loc[
                group["detector"].eq("isolation_forest")
                & group["session_gap_minutes"].eq(gap)
                & group["alert_budget"].eq("5%")
            ].empty for gap in EXPECTED_GAPS
        )
        record["selected_by_baseline_5pct_any_gap"] = any(
            not group.loc[
                group["detector"].eq("directional_robust_baseline")
                & group["session_gap_minutes"].eq(gap)
                & group["alert_budget"].eq("5%")
            ].empty for gap in EXPECTED_GAPS
        )
        record["selected_by_both_detectors_5pct"] = (
            record["selected_by_isolation_forest_5pct_any_gap"]
            and record["selected_by_baseline_5pct_any_gap"]
        )
        record["interpretation_bucket"] = (
            "both_detectors_5pct"
            if record["selected_by_both_detectors_5pct"]
            else (
                "isolation_forest_only_5pct"
                if record["selected_by_isolation_forest_5pct_any_gap"]
                else (
                    "baseline_only_5pct"
                    if record["selected_by_baseline_5pct_any_gap"]
                    else "not_selected_at_5pct"
                )
            )
        )
        records.append(record)

    consensus = pd.DataFrame(records)
    if not consensus.empty:
        consensus = consensus.sort_values(
            ["selected_in_combinations", "timestamp_utc"],
            ascending=[False, True],
            kind="stable",
        )

    # Summaries include event-level selection counts; these are stability measures,
    # not model-accuracy measures.
    summary_rows = []
    for bucket, group in consensus.groupby("interpretation_bucket", dropna=False):
        summary_rows.append({
            "summary_type": "5pct_detector_agreement",
            "group": bucket,
            "unique_events": len(group),
            "mean_selected_combinations_out_of_12": round(
                group["selected_in_combinations"].mean(), 3
            ),
            "max_selected_combinations_out_of_12": int(
                group["selected_in_combinations"].max()
            ),
            "interpretation": "selection stability/agreement only; not accuracy",
        })

    for detector in EXPECTED_DETECTORS:
        for budget in EXPECTED_BUDGETS:
            cols = [
                f"{detector}_gap{gap}_{budget.replace('%', 'pct')}_selected"
                for gap in EXPECTED_GAPS
            ]
            selected_in_both = int(consensus[cols].all(axis=1).sum()) if not consensus.empty else 0
            selected_in_either = int(consensus[cols].any(axis=1).sum()) if not consensus.empty else 0
            summary_rows.append({
                "summary_type": "session_gap_stability",
                "group": f"{detector} / {budget}",
                "unique_events": selected_in_either,
                "mean_selected_combinations_out_of_12": "",
                "max_selected_combinations_out_of_12": "",
                "events_selected_at_both_gaps": selected_in_both,
                "events_selected_at_either_gap": selected_in_either,
                "interpretation": "event membership consistency between 1m and 5m settings",
            })

    summary = pd.DataFrame(summary_rows)
    CONSENSUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    consensus.to_csv(CONSENSUS_PATH, index=False, encoding="utf-8-sig")
    summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")

    print("=" * 72)
    print("KBR V5 EVENT CONSENSUS / DISAGREEMENT ANALYSIS")
    print("=" * 72)
    print(f"Selected-event input rows: {len(data)}")
    print(f"Unique event keys: {len(consensus)}")
    print(f"Events selected by both detectors at 5% (either session setting): "
          f"{int(consensus['selected_by_both_detectors_5pct'].sum()) if not consensus.empty else 0}")
    print(f"Events selected by Isolation Forest at 5% (either setting): "
          f"{int(consensus['selected_by_isolation_forest_5pct_any_gap'].sum()) if not consensus.empty else 0}")
    print(f"Events selected by baseline at 5% (either setting): "
          f"{int(consensus['selected_by_baseline_5pct_any_gap'].sum()) if not consensus.empty else 0}")
    print(f"Consensus report: {CONSENSUS_PATH.relative_to(ROOT)}")
    print(f"Summary report: {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Input SHA-256: {sha256_file(INPUT_PATH)}")
    print("Ground-truth labels inferred: False")
    print("Models retrained: False")
    print("Production models modified: False")
    print("Existing risk report modified: False")
    print()
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
