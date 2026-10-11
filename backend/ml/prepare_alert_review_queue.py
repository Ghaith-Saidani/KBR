"""
Create a manual review queue for the 47 unique V5 selected alert anchors.

Run from the KBR project root:
    python -m backend.ml.prepare_alert_review_queue

Inputs:
    data/reports/business_detector_alert_context_summary.csv
    data/reports/business_detector_alert_episode_members_v2.csv

Output:
    data/reports/business_detector_alert_review_queue.csv

The CSV is intended for manual review in Excel. Review labels are blank by design:
    expected_activity
    suspicious_needs_investigation
    likely_test_or_development
    unclear

This script does not infer ground truth and does not modify models or risk reports.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
SUMMARY_PATH = ROOT / "data" / "reports" / "business_detector_alert_context_summary.csv"
MEMBERS_PATH = ROOT / "data" / "reports" / "business_detector_alert_episode_members_v2.csv"
OUTPUT_PATH = ROOT / "data" / "reports" / "business_detector_alert_review_queue.csv"

REVIEW_LABELS = [
    "expected_activity",
    "suspicious_needs_investigation",
    "likely_test_or_development",
    "unclear",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"Missing summary file: {SUMMARY_PATH}")
    if not MEMBERS_PATH.exists():
        raise FileNotFoundError(f"Missing corrected episode members file: {MEMBERS_PATH}")

    summary = pd.read_csv(SUMMARY_PATH, low_memory=False)
    members = pd.read_csv(MEMBERS_PATH, low_memory=False)

    if "anchor_id" not in summary.columns or "anchor_id" not in members.columns:
        raise ValueError("Both inputs must contain anchor_id.")

    # Keep one row per unique anchor, even if an input was accidentally duplicated.
    summary = summary.drop_duplicates(subset=["anchor_id"], keep="first").copy()
    members = members.drop_duplicates(subset=["anchor_id"], keep="first").copy()

    episode_columns = [
        "anchor_id",
        "episode_id",
        "gap_from_previous_same_identity_seconds",
        "episode_number_within_identity",
    ]
    episode_columns = [c for c in episode_columns if c in members.columns]
    episode_info = members[episode_columns].copy()

    queue = summary.merge(episode_info, on="anchor_id", how="left", suffixes=("", "_episode"))

    if "anchor_timestamp" in queue.columns:
        queue["anchor_timestamp"] = pd.to_datetime(
            queue["anchor_timestamp"], errors="coerce", format="mixed", utc=True
        )
        queue = queue.sort_values(
            ["anchor_timestamp", "anchor_id"], kind="stable"
        )

    # Manual fields intentionally remain blank. Do not auto-label based on heuristics.
    queue["review_label"] = ""
    queue["review_reason"] = ""
    queue["reviewer_notes"] = ""
    queue["reviewed"] = False

    # Helpful label definitions included in each row so the CSV remains self-contained.
    queue["review_label_guide"] = (
        "expected_activity=known/normal; "
        "suspicious_needs_investigation=unexplained pattern requiring follow-up; "
        "likely_test_or_development=likely test/local-development artifact; "
        "unclear=insufficient evidence"
    )

    # Put review columns and the most useful fields first.
    preferred = [
        "anchor_id",
        "anchor_timestamp",
        "episode_id",
        "selected_detectors",
        "selected_gap_settings",
        "selected_ranks",
        "anchor_action",
        "anchor_resource_type",
        "anchor_method",
        "anchor_endpoint",
        "anchor_ip_address",
        "anchor_user_id",
        "anchor_user_agent",
        "context_events_2min",
        "events_before_anchor",
        "events_after_anchor",
        "events_same_user",
        "events_same_ip",
        "distinct_user_ids",
        "distinct_ip_addresses",
        "top_actions",
        "resource_type_counts",
        "response_status_counts",
        "gap_from_previous_same_identity_seconds",
        "review_label",
        "review_reason",
        "reviewer_notes",
        "reviewed",
        "review_label_guide",
    ]
    columns = [c for c in preferred if c in queue.columns]
    columns.extend(c for c in queue.columns if c not in columns)
    queue = queue[columns]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    queue.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("=" * 72)
    print("KBR V5 MANUAL ALERT REVIEW QUEUE")
    print("=" * 72)
    print(f"Unique alert anchors: {len(queue)}")
    print(f"Rows with episode mapping: {int(queue['episode_id'].notna().sum()) if 'episode_id' in queue.columns else 0}")
    print(f"Review labels available: {', '.join(REVIEW_LABELS)}")
    print(f"Output: {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Summary SHA-256: {sha256_file(SUMMARY_PATH)}")
    print(f"Episode members SHA-256: {sha256_file(MEMBERS_PATH)}")
    print("Review labels assigned automatically: False")
    print("Production models modified: False")
    print("Existing risk report modified: False")


if __name__ == "__main__":
    main()
