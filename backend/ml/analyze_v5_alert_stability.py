"""
Run a separate V5 robustness and stability diagnostic.

Run from the KBR project root:
    python -m backend.ml.analyze_v5_alert_stability

Inputs:
    data/reports/business_detector_benchmark_v5.json
    data/processed/user_activities.csv
    data/reports/business_detector_alert_episode_members_v2.csv (optional)

Outputs:
    data/reports/business_detector_v5_alert_stability.csv
    data/reports/business_detector_v5_stability_summary.csv

This script:
- Compares selected alerts across 1-minute and 5-minute session definitions.
- Summarizes IP/user/action patterns at 1%, 2%, and 5% alert budgets.
- Computes overlap/Jaccard for the same detector and budget across session settings.
- Optionally reports the already-generated provisional episode count.
- Does not train models or modify production models/risk reports.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path.cwd()
BENCHMARK_PATH = ROOT / "data" / "reports" / "business_detector_benchmark_v5.json"
DATASET_PATH = ROOT / "data" / "processed" / "user_activities.csv"
EPISODE_MEMBERS_PATH = ROOT / "data" / "reports" / "business_detector_alert_episode_members_v2.csv"
ALERT_OUTPUT_PATH = ROOT / "data" / "reports" / "business_detector_v5_alert_stability.csv"
SUMMARY_OUTPUT_PATH = ROOT / "data" / "reports" / "business_detector_v5_stability_summary.csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().fillna("")


def event_key(timestamp: Any, action: Any, method: Any, resource_type: Any) -> tuple[str, str, str, str]:
    parsed = pd.to_datetime(timestamp, errors="coerce", format="mixed", utc=True)
    ts = parsed.isoformat() if not pd.isna(parsed) else str(timestamp)
    return (
        ts,
        str(action or "").strip().lower(),
        str(method or "").strip().lower(),
        str(resource_type or "").strip().lower(),
    )


def join_unique(values: pd.Series) -> str:
    return "; ".join(sorted({
        str(v).strip() for v in values.dropna() if str(v).strip()
    }))


def main() -> None:
    for path in [BENCHMARK_PATH, DATASET_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")

    report = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    raw = pd.read_csv(DATASET_PATH, low_memory=False)

    timestamp_col = next(
        (c for c in ["created_at", "timestamp", "occurred_at", "event_time"] if c in raw.columns),
        None,
    )
    action_col = next((c for c in ["action", "event_type", "activity"] if c in raw.columns), None)
    resource_col = next((c for c in ["resource_type", "resource", "category"] if c in raw.columns), None)
    method_col = next((c for c in ["method", "http_method"] if c in raw.columns), None)
    user_col = next((c for c in ["user_id", "actor_id"] if c in raw.columns), None)
    ip_col = next((c for c in ["ip_address", "client_ip", "ip"] if c in raw.columns), None)
    endpoint_col = next((c for c in ["endpoint", "path", "resource_path"] if c in raw.columns), None)

    if not timestamp_col or not action_col or not resource_col:
        raise ValueError("Dataset lacks required timestamp/action/resource columns.")

    raw["_ts"] = pd.to_datetime(raw[timestamp_col], errors="coerce", format="mixed", utc=True)
    raw["_action_norm"] = normalize(raw[action_col])
    raw["_resource_norm"] = normalize(raw[resource_col])
    raw["_method_norm"] = normalize(raw[method_col]) if method_col else ""
    raw = raw.loc[raw["_ts"].notna()].copy()

    # Match the benchmark's business-only population.
    business = raw.loc[~raw["_resource_norm"].eq("http_request")].copy()
    source_groups: dict[tuple[str, str, str, str], list[int]] = {}
    for idx, row in business.iterrows():
        key = event_key(row["_ts"], row[action_col],
                        row[method_col] if method_col else "",
                        row[resource_col])
        source_groups.setdefault(key, []).append(idx)

    output_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    selected_sets: dict[tuple[str, str, str], set[tuple[str, str, str, str]]] = {}

    results = report.get("results_by_session_gap_minutes", {})
    for gap in sorted(results, key=lambda x: int(x)):
        detectors = results[gap].get("detectors", {})
        for detector_name, detector_data in detectors.items():
            budgets = detector_data.get("fixed_alert_budgets", {})
            for budget in ["1%", "2%", "5%"]:
                budget_data = budgets.get(budget, {})
                alerts = budget_data.get("selected_alerts", [])
                keys: set[tuple[str, str, str, str]] = set()

                for rank, alert in enumerate(alerts, start=1):
                    key = event_key(
                        alert.get("timestamp", ""),
                        alert.get("action", ""),
                        alert.get("method", ""),
                        alert.get("resource_type", ""),
                    )
                    keys.add(key)
                    matched_rows = source_groups.get(key, [])
                    source = business.loc[matched_rows[0]] if len(matched_rows) == 1 else None

                    row: dict[str, Any] = {
                        "session_gap_minutes": int(gap),
                        "detector": detector_name,
                        "alert_budget": budget,
                        "rank": rank,
                        "timestamp_utc": key[0],
                        "action": alert.get("action", ""),
                        "method": alert.get("method", ""),
                        "resource_type": alert.get("resource_type", ""),
                        "score": alert.get("score"),
                        "source_match_count": len(matched_rows),
                        "source_match_status": (
                            "unique" if len(matched_rows) == 1
                            else ("not_found" if len(matched_rows) == 0 else "ambiguous")
                        ),
                    }
                    if source is not None:
                        row["user_id"] = source[user_col] if user_col else ""
                        row["ip_address"] = source[ip_col] if ip_col else ""
                        row["endpoint"] = source[endpoint_col] if endpoint_col else ""
                    else:
                        row["user_id"] = ""
                        row["ip_address"] = ""
                        row["endpoint"] = ""
                    output_rows.append(row)

                selected_sets[(str(gap), detector_name, budget)] = keys
                ip_counts = pd.Series([
                    r["ip_address"] for r in output_rows
                    if r["session_gap_minutes"] == int(gap)
                    and r["detector"] == detector_name
                    and r["alert_budget"] == budget
                    and str(r["ip_address"]).strip()
                ]).value_counts()
                user_counts = pd.Series([
                    r["user_id"] for r in output_rows
                    if r["session_gap_minutes"] == int(gap)
                    and r["detector"] == detector_name
                    and r["alert_budget"] == budget
                    and str(r["user_id"]).strip()
                ]).value_counts()

                summary_rows.append({
                    "session_gap_minutes": int(gap),
                    "detector": detector_name,
                    "alert_budget": budget,
                    "evaluation_rows": budget_data.get("evaluation_count"),
                    "selected_alert_count": len(alerts),
                    "distinct_selected_events": len(keys),
                    "distinct_ip_labels": len(ip_counts),
                    "ip_label_counts": "; ".join(f"{k} ({v})" for k, v in ip_counts.items()),
                    "distinct_users": len(user_counts),
                    "top_user_counts": "; ".join(f"{k} ({v})" for k, v in user_counts.head(5).items()),
                    "resource_type_counts": json.dumps(
                        budget_data.get("selected_category_counts_top_10", {}).get("resource_type", {}),
                        ensure_ascii=False,
                    ),
                    "selected_time_start": budget_data.get("selected_timestamp_start"),
                    "selected_time_end": budget_data.get("selected_timestamp_end"),
                })

    # Compare rankings at the same budget for each detector across 1m and 5m settings.
    for detector_name in sorted({
        row["detector"] for row in summary_rows
    }):
        for budget in ["1%", "2%", "5%"]:
            set_1 = selected_sets.get(("1", detector_name, budget), set())
            set_5 = selected_sets.get(("5", detector_name, budget), set())
            intersection = set_1 & set_5
            union = set_1 | set_5
            jaccard = len(intersection) / len(union) if union else 1.0
            summary_rows.append({
                "session_gap_minutes": "1m_vs_5m",
                "detector": detector_name,
                "alert_budget": budget,
                "evaluation_rows": "",
                "selected_alert_count": "",
                "distinct_selected_events": "",
                "distinct_ip_labels": "",
                "ip_label_counts": "",
                "distinct_users": "",
                "top_user_counts": "",
                "resource_type_counts": "",
                "selected_time_start": "",
                "selected_time_end": "",
                "overlap_count": len(intersection),
                "union_count": len(union),
                "jaccard_pct": round(jaccard * 100, 2),
                "only_1m_count": len(set_1 - set_5),
                "only_5m_count": len(set_5 - set_1),
                "shared_events": " || ".join(" | ".join(k) for k in sorted(intersection)),
            })

    episode_count = None
    if EPISODE_MEMBERS_PATH.exists():
        episodes = pd.read_csv(EPISODE_MEMBERS_PATH, low_memory=False)
        if "episode_id" in episodes.columns:
            episode_count = int(episodes["episode_id"].nunique())

    alert_df = pd.DataFrame(output_rows)
    summary_df = pd.DataFrame(summary_rows)
    if episode_count is not None:
        summary_df["provisional_episode_count_from_v2"] = episode_count
    else:
        summary_df["provisional_episode_count_from_v2"] = ""

    ALERT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    alert_df.to_csv(ALERT_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    summary_df.to_csv(SUMMARY_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("=" * 72)
    print("KBR V5 ALERT STABILITY DIAGNOSTIC")
    print("=" * 72)
    print(f"Benchmark report: {BENCHMARK_PATH.relative_to(ROOT)}")
    print(f"Business source rows: {len(business)}")
    print(f"Alert selections expanded: {len(alert_df)}")
    print(f"Unique source matches: {int(alert_df['source_match_status'].eq('unique').sum())}")
    print(f"Missing source matches: {int(alert_df['source_match_status'].eq('not_found').sum())}")
    print(f"Ambiguous source matches: {int(alert_df['source_match_status'].eq('ambiguous').sum())}")
    if episode_count is not None:
        print(f"Existing provisional episode count (v2): {episode_count}")
    print(f"Alert details: {ALERT_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Summary: {SUMMARY_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Benchmark SHA-256: {sha256_file(BENCHMARK_PATH)}")
    print(f"Dataset SHA-256: {sha256_file(DATASET_PATH)}")
    print("Models retrained: False")
    print("Production models modified: False")
    print("Existing risk report modified: False")
    print()
    overlap_rows = summary_df.loc[summary_df["session_gap_minutes"].astype(str).eq("1m_vs_5m")]
    if not overlap_rows.empty:
        print("Ranking stability (same event key, same detector/budget):")
        cols = ["detector", "alert_budget", "overlap_count", "union_count", "jaccard_pct"]
        print(overlap_rows[cols].to_string(index=False))


if __name__ == "__main__":
    main()
