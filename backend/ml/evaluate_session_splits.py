
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

DATASET = Path("data/processed/user_activities.csv")
OUTPUT = Path("data/reports/session_split_candidates.json")

GAP_THRESHOLDS_MINUTES = (1, 5, 15, 30)
TRAIN_SESSION_FRACTION = 0.80


def analyze_population(
    frame: pd.DataFrame,
    population: str,
    gap_minutes: int,
) -> dict:
    frame = frame.sort_values("occurred_at").copy().reset_index(drop=True)

    if frame.empty:
        return {"population": population, "rows": 0}

    gaps = frame["occurred_at"].diff()
    new_session = gaps.isna() | (
        gaps > pd.Timedelta(minutes=gap_minutes)
    )
    frame["session_id"] = new_session.cumsum()

    sessions = (
        frame.groupby("session_id", sort=True)
        .agg(
            start=("occurred_at", "min"),
            end=("occurred_at", "max"),
            rows=("occurred_at", "size"),
        )
        .reset_index()
    )

    session_count = len(sessions)
    split_index = max(
        1,
        min(
            session_count - 1,
            int(session_count * TRAIN_SESSION_FRACTION),
        ),
    ) if session_count >= 2 else session_count

    if session_count >= 2:
        train_sessions = sessions.iloc[:split_index]
        eval_sessions = sessions.iloc[split_index:]

        train_ids = set(train_sessions["session_id"])
        eval_ids = set(eval_sessions["session_id"])

        train_rows = frame[frame["session_id"].isin(train_ids)]
        eval_rows = frame[frame["session_id"].isin(eval_ids)]

        split = {
            "training_sessions": len(train_sessions),
            "evaluation_sessions": len(eval_sessions),
            "training_rows": len(train_rows),
            "evaluation_rows": len(eval_rows),
            "training_active_days": int(
                train_rows["occurred_at"].dt.normalize().nunique()
            ),
            "evaluation_active_days": int(
                eval_rows["occurred_at"].dt.normalize().nunique()
            ),
            "training_start": str(train_rows["occurred_at"].min()),
            "training_end": str(train_rows["occurred_at"].max()),
            "evaluation_start": str(eval_rows["occurred_at"].min()),
            "evaluation_end": str(eval_rows["occurred_at"].max()),
            "sessions_crossing_split": len(
                train_ids.intersection(eval_ids)
            ),
        }
    else:
        split = {
            "warning": "Not enough sessions for a train/evaluation split."
        }

    return {
        "population": population,
        "gap_threshold_minutes": gap_minutes,
        "rows": len(frame),
        "session_count": session_count,
        "single_event_sessions": int(
            (sessions["rows"] == 1).sum()
        ),
        "sessions_with_2plus_events": int(
            (sessions["rows"] >= 2).sum()
        ),
        "sessions_with_10plus_events": int(
            (sessions["rows"] >= 10).sum()
        ),
        "largest_session_rows": int(sessions["rows"].max()),
        "largest_session_fraction_pct": round(
            sessions["rows"].max() / len(frame) * 100, 2
        ),
        "grouped_chronological_split": split,
    }


def main() -> None:
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET}")

    df = pd.read_csv(DATASET)

    required = {"occurred_at", "resource_type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["occurred_at"] = pd.to_datetime(
        df["occurred_at"],
        format="mixed",
        errors="coerce",
        utc=True,
    )
    df = df.dropna(subset=["occurred_at"]).sort_values("occurred_at")

    populations = {
        "http": df[df["resource_type"] == "http_request"],
        "business": df[df["resource_type"] != "http_request"],
    }

    results = []
    for gap in GAP_THRESHOLDS_MINUTES:
        for name, population_frame in populations.items():
            results.append(
                analyze_population(population_frame, name, gap)
            )

    report = {
        "dataset": str(DATASET),
        "valid_rows": len(df),
        "training_session_fraction": TRAIN_SESSION_FRACTION,
        "thresholds_minutes": list(GAP_THRESHOLDS_MINUTES),
        "interpretation": (
            "Sessions are time-based groups, not confirmed incidents. "
            "This report tests split feasibility only; it does not "
            "measure model accuracy."
        ),
        "results": results,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== SESSION SPLIT CANDIDATES ===")
    print(f"Dataset rows: {len(df)}")

    for result in results:
        split = result.get("grouped_chronological_split", {})
        print(
            f"\n{result['population'].upper()} | "
            f"gap={result['gap_threshold_minutes']} min"
        )
        print(
            f"Sessions: {result['session_count']} | "
            f"single-event: {result['single_event_sessions']} | "
            f"2+ events: {result['sessions_with_2plus_events']} | "
            f"10+ events: {result['sessions_with_10plus_events']}"
        )
        print(
            f"Largest session: {result['largest_session_rows']} rows "
            f"({result['largest_session_fraction_pct']}%)"
        )

        if "warning" in split:
            print(split["warning"])
        else:
            print(
                f"Train: {split['training_sessions']} sessions / "
                f"{split['training_rows']} rows / "
                f"{split['training_active_days']} active days"
            )
            print(
                f"Eval:  {split['evaluation_sessions']} sessions / "
                f"{split['evaluation_rows']} rows / "
                f"{split['evaluation_active_days']} active days"
            )
            print(
                f"Evaluation starts: {split['evaluation_start']}"
            )
            print(
                f"Sessions crossing split: "
                f"{split['sessions_crossing_split']}"
            )

    print(f"\nReport saved to: {OUTPUT.resolve()}")
    print("No models or existing reports were modified.")


if __name__ == "__main__":
    main()
