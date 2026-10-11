"""
Aggregate selected V5 alert events into time-based episodes.

Run from the KBR project root:
    python -m backend.ml.aggregate_alert_episodes

Input:
    data/reports/business_detector_alert_context_summary.csv

Outputs:
    data/reports/business_detector_alert_episodes.csv
    data/reports/business_detector_alert_episode_members.csv

Episode rule:
    Sort selected alert anchors by IP label and timestamp. Consecutive anchors
    with the same IP label belong to the same episode while the gap between
    consecutive anchors is <= 120 seconds. A larger gap starts a new episode.

This is a diagnostic grouping rule, not a claim that each episode is an incident.
No production model or risk report is modified.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
INPUT_PATH = ROOT / "data" / "reports" / "business_detector_alert_context_summary.csv"
EPISODES_PATH = ROOT / "data" / "reports" / "business_detector_alert_episodes.csv"
MEMBERS_PATH = ROOT / "data" / "reports" / "business_detector_alert_episode_members.csv"

MAX_GAP_SECONDS = 120


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def join_unique(values: pd.Series) -> str:
    items = sorted({
        str(value).strip()
        for value in values.dropna()
        if str(value).strip()
    })
    return "; ".join(items)


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input not found: {INPUT_PATH}\n"
            "Run backend.ml.inspect_alert_context_timed first."
        )

    summary = pd.read_csv(INPUT_PATH, low_memory=False)
    required = {"anchor_id", "anchor_timestamp", "anchor_ip_address", "anchor_action"}
    missing = required - set(summary.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    summary["anchor_timestamp"] = pd.to_datetime(
        summary["anchor_timestamp"], errors="coerce", format="mixed", utc=True
    )
    summary = summary.loc[summary["anchor_timestamp"].notna()].copy()

    # IP is treated as a grouping label. Values such as "testclient" are not
    # interpreted as real network IP addresses.
    summary["ip_group"] = (
        summary["anchor_ip_address"].astype("string").str.strip().fillna("")
    )
    summary.loc[summary["ip_group"].eq(""), "ip_group"] = "(missing IP label)"
    summary = summary.sort_values(
        ["ip_group", "anchor_timestamp", "anchor_id"], kind="stable"
    ).reset_index(drop=True)

    summary["gap_from_previous_seconds"] = (
        summary.groupby("ip_group", sort=False)["anchor_timestamp"]
        .diff()
        .dt.total_seconds()
    )
    new_episode = (
        summary["gap_from_previous_seconds"].isna()
        | summary["gap_from_previous_seconds"].gt(MAX_GAP_SECONDS)
    )
    summary["episode_number_within_ip"] = new_episode.groupby(
        summary["ip_group"], sort=False
    ).cumsum().astype(int)
    summary["episode_id"] = summary.apply(
        lambda row: f"EP-{row['ip_group']}-{row['episode_number_within_ip']:03d}",
        axis=1,
    )

    episode_rows = []
    for episode_id, group in summary.groupby("episode_id", sort=False):
        group = group.sort_values("anchor_timestamp", kind="stable")
        first = group.iloc[0]
        last = group.iloc[-1]
        span_seconds = (
            last["anchor_timestamp"] - first["anchor_timestamp"]
        ).total_seconds()

        episode_rows.append({
            "episode_id": episode_id,
            "ip_group": first["ip_group"],
            "episode_start_utc": first["anchor_timestamp"],
            "episode_end_utc": last["anchor_timestamp"],
            "duration_seconds": span_seconds,
            "alert_anchor_count": len(group),
            "unique_anchor_actions": group["anchor_action"].nunique(dropna=True),
            "resource_types": join_unique(group["anchor_resource_type"])
                if "anchor_resource_type" in group.columns else "",
            "anchor_actions": join_unique(group["anchor_action"]),
            "detectors_involved": join_unique(group["selected_detectors"])
                if "selected_detectors" in group.columns else "",
            "user_ids_observed": join_unique(group["anchor_user_id"])
                if "anchor_user_id" in group.columns else "",
            "endpoints_observed": join_unique(group["anchor_endpoint"])
                if "anchor_endpoint" in group.columns else "",
            "response_status_patterns": join_unique(group["response_status_counts"])
                if "response_status_counts" in group.columns else "",
            "max_gap_between_alerts_seconds": (
                float(group["gap_from_previous_seconds"].dropna().max())
                if group["gap_from_previous_seconds"].notna().any() else 0.0
            ),
            "grouping_rule": f"same IP label, consecutive alert gap <= {MAX_GAP_SECONDS}s",
            "interpretation": "time-based alert cluster; not a confirmed incident",
        })

    episodes = pd.DataFrame(episode_rows)
    members = summary.copy()
    members = members.rename(columns={
        "anchor_timestamp": "anchor_timestamp_utc",
        "ip_group": "episode_ip_group",
    })
    members["episode_gap_threshold_seconds"] = MAX_GAP_SECONDS
    members["episode_interpretation"] = "time-based alert cluster; not a confirmed incident"

    episodes = episodes.sort_values(
        ["episode_start_utc", "episode_id"], kind="stable"
    ).reset_index(drop=True)
    members = members.sort_values(
        ["anchor_timestamp_utc", "episode_id", "anchor_id"], kind="stable"
    ).reset_index(drop=True)

    EPISODES_PATH.parent.mkdir(parents=True, exist_ok=True)
    episodes.to_csv(EPISODES_PATH, index=False, encoding="utf-8-sig")
    members.to_csv(MEMBERS_PATH, index=False, encoding="utf-8-sig")

    print("=" * 72)
    print("KBR V5 ALERT EPISODE AGGREGATION")
    print("=" * 72)
    print(f"Alert anchors: {len(summary)}")
    print(f"Episode count: {len(episodes)}")
    print(f"IP/group labels: {summary['ip_group'].nunique()}")
    print(f"Maximum gap within an episode: {MAX_GAP_SECONDS} seconds")
    print(f"Largest episode: {int(episodes['alert_anchor_count'].max()) if not episodes.empty else 0} anchors")
    print(f"Input SHA-256: {sha256_file(INPUT_PATH)}")
    print(f"Episodes output: {EPISODES_PATH.relative_to(ROOT)}")
    print(f"Episode members output: {MEMBERS_PATH.relative_to(ROOT)}")
    print("Production models modified: False")
    print("Existing risk report modified: False")
    print()
    if not episodes.empty:
        print("Largest episodes:")
        print(
            episodes.nlargest(10, "alert_anchor_count")[
                ["episode_id", "ip_group", "episode_start_utc",
                 "episode_end_utc", "duration_seconds", "alert_anchor_count",
                 "detectors_involved", "resource_types"]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
