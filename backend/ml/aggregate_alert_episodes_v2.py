"""
Corrected aggregation of selected V5 alerts into provisional episodes.

Run from the KBR project root:
    python -m backend.ml.aggregate_alert_episodes_v2

Input:
    data/reports/business_detector_alert_context_summary.csv

Outputs:
    data/reports/business_detector_alert_episodes_v2.csv
    data/reports/business_detector_alert_episode_members_v2.csv

Grouping:
    Same IP label AND same user ID, with consecutive selected alert anchors
    no more than 120 seconds apart.

This is a diagnostic clustering heuristic, not ground-truth incident labeling.
Production models and the existing risk report are not modified.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
INPUT_PATH = ROOT / "data" / "reports" / "business_detector_alert_context_summary.csv"
EPISODES_PATH = ROOT / "data" / "reports" / "business_detector_alert_episodes_v2.csv"
MEMBERS_PATH = ROOT / "data" / "reports" / "business_detector_alert_episode_members_v2.csv"

MAX_GAP_SECONDS = 120


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_semicolon_values(values: pd.Series) -> str:
    unique: set[str] = set()
    for value in values.dropna():
        for item in str(value).split(";"):
            item = item.strip()
            if item:
                unique.add(item)
    return "; ".join(sorted(unique))


def join_values(values: pd.Series) -> str:
    return "; ".join(sorted({
        str(value).strip()
        for value in values.dropna()
        if str(value).strip()
    }))


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input not found: {INPUT_PATH}\n"
            "Run backend.ml.inspect_alert_context_timed first."
        )

    data = pd.read_csv(INPUT_PATH, low_memory=False)
    required = {"anchor_id", "anchor_timestamp", "anchor_ip_address", "anchor_action"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data["anchor_timestamp"] = pd.to_datetime(
        data["anchor_timestamp"], errors="coerce", format="mixed", utc=True
    )
    data = data.loc[data["anchor_timestamp"].notna()].copy()

    data["ip_group"] = data["anchor_ip_address"].astype("string").str.strip().fillna("")
    data.loc[data["ip_group"].eq(""), "ip_group"] = "(missing IP label)"

    if "anchor_user_id" in data.columns:
        data["user_group"] = data["anchor_user_id"].astype("string").str.strip().fillna("")
    else:
        data["user_group"] = ""
    data.loc[data["user_group"].eq(""), "user_group"] = "(missing user ID)"

    # A unique anchor should appear once. Keep the first if the input has duplicates.
    data = data.sort_values(
        ["anchor_timestamp", "anchor_id"], kind="stable"
    ).drop_duplicates(subset=["anchor_id"], keep="first")

    data = data.sort_values(
        ["ip_group", "user_group", "anchor_timestamp", "anchor_id"], kind="stable"
    ).reset_index(drop=True)

    grouping = ["ip_group", "user_group"]
    data["gap_from_previous_same_identity_seconds"] = (
        data.groupby(grouping, sort=False)["anchor_timestamp"]
        .diff()
        .dt.total_seconds()
    )

    starts_episode = (
        data["gap_from_previous_same_identity_seconds"].isna()
        | data["gap_from_previous_same_identity_seconds"].gt(MAX_GAP_SECONDS)
    )
    data["episode_number_within_identity"] = (
        starts_episode.groupby([data["ip_group"], data["user_group"]], sort=False)
        .cumsum()
        .astype(int)
    )

    def episode_id(row: pd.Series) -> str:
        # Hash user/IP labels to keep IDs concise and safe for CSV consumers.
        identity = f"{row['ip_group']}|{row['user_group']}"
        short_hash = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:8]
        return f"EP-{short_hash}-{int(row['episode_number_within_identity']):03d}"

    data["episode_id"] = data.apply(episode_id, axis=1)

    episode_records = []
    for ep_id, group in data.groupby("episode_id", sort=False):
        group = group.sort_values("anchor_timestamp", kind="stable")
        first = group.iloc[0]
        last = group.iloc[-1]
        internal_gaps = group["anchor_timestamp"].diff().dt.total_seconds().dropna()

        episode_records.append({
            "episode_id": ep_id,
            "ip_group": first["ip_group"],
            "user_group": first["user_group"],
            "episode_start_utc": first["anchor_timestamp"],
            "episode_end_utc": last["anchor_timestamp"],
            "duration_seconds": (
                last["anchor_timestamp"] - first["anchor_timestamp"]
            ).total_seconds(),
            "alert_anchor_count": len(group),
            "unique_anchor_actions": group["anchor_action"].nunique(dropna=True),
            "resource_types": join_values(group["anchor_resource_type"])
                if "anchor_resource_type" in group.columns else "",
            "anchor_actions": join_values(group["anchor_action"]),
            "detectors_involved": split_semicolon_values(group["selected_detectors"])
                if "selected_detectors" in group.columns else "",
            "anchor_endpoints": join_values(group["anchor_endpoint"])
                if "anchor_endpoint" in group.columns else "",
            "max_internal_gap_seconds": (
                float(internal_gaps.max()) if not internal_gaps.empty else 0.0
            ),
            "grouping_rule": (
                f"same IP label + same user ID; consecutive alert gap <= {MAX_GAP_SECONDS}s"
            ),
            "interpretation": "provisional time-based alert cluster; not a confirmed incident",
        })

    episodes = pd.DataFrame(episode_records)
    members = data.copy()
    members = members.rename(columns={"anchor_timestamp": "anchor_timestamp_utc"})
    members["episode_gap_threshold_seconds"] = MAX_GAP_SECONDS
    members["episode_interpretation"] = (
        "provisional time-based alert cluster; not a confirmed incident"
    )

    if not episodes.empty:
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
    print("KBR V5 CORRECTED ALERT EPISODE AGGREGATION")
    print("=" * 72)
    print(f"Unique alert anchors: {len(data)}")
    print(f"Provisional episodes: {len(episodes)}")
    print(f"Distinct IP labels: {data['ip_group'].nunique()}")
    print(f"Distinct IP/user identity pairs: {data[grouping].drop_duplicates().shape[0]}")
    print(f"Grouping threshold: {MAX_GAP_SECONDS} seconds")
    print(f"Input SHA-256: {sha256_file(INPUT_PATH)}")
    print(f"Episodes output: {EPISODES_PATH.relative_to(ROOT)}")
    print(f"Members output: {MEMBERS_PATH.relative_to(ROOT)}")
    print("Production models modified: False")
    print("Existing risk report modified: False")
    if not episodes.empty:
        print()
        print("Largest episodes:")
        print(episodes.nlargest(10, "alert_anchor_count")[
            ["episode_id", "ip_group", "user_group", "episode_start_utc",
             "episode_end_utc", "duration_seconds", "alert_anchor_count",
             "detectors_involved", "resource_types", "max_internal_gap_seconds"]
        ].to_string(index=False))


if __name__ == "__main__":
    main()
