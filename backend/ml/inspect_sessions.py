
from pathlib import Path
import json

import pandas as pd

DATASET = Path("data/processed/user_activities.csv")
OUTPUT = Path("data/reports/session_inspection_report.json")
GAP_MINUTES = 5


def inspect_sessions(frame: pd.DataFrame, name: str) -> dict:
    frame = frame.sort_values("occurred_at").copy()

    if frame.empty:
        return {"population": name, "rows": 0, "sessions": []}

    gaps = frame["occurred_at"].diff()
    frame["session_id"] = (
        gaps.isna() | (gaps > pd.Timedelta(minutes=GAP_MINUTES))
    ).cumsum()

    sessions = (
        frame.groupby("session_id")
        .agg(
            rows=("occurred_at", "size"),
            start=("occurred_at", "min"),
            end=("occurred_at", "max"),
        )
        .reset_index(drop=True)
    )

    sessions["duration_seconds"] = (
        sessions["end"] - sessions["start"]
    ).dt.total_seconds()

    sessions["start"] = sessions["start"].astype(str)
    sessions["end"] = sessions["end"].astype(str)

    sizes = sessions["rows"]

    return {
        "population": name,
        "rows": len(frame),
        "session_gap_minutes": GAP_MINUTES,
        "session_count": len(sessions),
        "single_event_sessions": int((sizes == 1).sum()),
        "sessions_with_2_or_more_events": int((sizes >= 2).sum()),
        "sessions_with_10_or_more_events": int((sizes >= 10).sum()),
        "largest_session_rows": int(sizes.max()),
        "median_session_rows": float(sizes.median()),
        "top_sessions": (
            sessions.sort_values("rows", ascending=False)
            .head(20)
            .to_dict(orient="records")
        ),
    }


def main() -> None:
    df = pd.read_csv(DATASET)
    df["occurred_at"] = pd.to_datetime(
        df["occurred_at"],
        format="mixed",
        errors="coerce",
        utc=True,
    )
    df = df.dropna(subset=["occurred_at"]).sort_values("occurred_at")

    http = df[df["resource_type"] == "http_request"]
    business = df[df["resource_type"] != "http_request"]

    report = {
        "dataset_rows": len(df),
        "session_gap_minutes": GAP_MINUTES,
        "interpretation": (
            "Sessions are temporal groupings, not confirmed real-world "
            "incidents. Their boundaries depend on the configured gap."
        ),
        "populations": {
            "http": inspect_sessions(http, "http"),
            "business": inspect_sessions(business, "business"),
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for name, result in report["populations"].items():
        print(f"\n--- {name.upper()} ---")
        print(f"Rows: {result['rows']}")
        print(f"Sessions: {result['session_count']}")
        print(f"Single-event sessions: {result['single_event_sessions']}")
        print(
            "Sessions with 2+ events:",
            result["sessions_with_2_or_more_events"],
        )
        print(
            "Sessions with 10+ events:",
            result["sessions_with_10_or_more_events"],
        )
        print("Largest session:", result["largest_session_rows"])
        print("Largest sessions:")
        for session in result["top_sessions"][:10]:
            print(
                f"  {session['start']} | "
                f"{session['rows']} events | "
                f"{session['duration_seconds']:.1f}s"
            )

    print(f"\nReport saved to: {OUTPUT.resolve()}")
    print("No dataset, model, or risk report was modified.")


if __name__ == "__main__":
    main()
