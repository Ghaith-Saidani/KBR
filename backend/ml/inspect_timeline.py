from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


DATASET_PATH = Path("data/processed/user_activities.csv")
REPORT_PATH = Path("data/reports/timeline_inspection_report.json")
DAILY_CSV_PATH = Path("data/reports/timeline_daily_counts.csv")

TIMESTAMP_COLUMN = "occurred_at"
POPULATION_COLUMN = "resource_type"
HTTP_VALUE = "http_request"
ACTION_COLUMN = "action"


def percentile(values: pd.Series, q: float):
    if values.empty:
        return None
    return round(float(values.quantile(q)), 4)


def inspect_population(
    frame: pd.DataFrame,
    population_name: str,
) -> dict:
    frame = frame.sort_values(TIMESTAMP_COLUMN).copy()
    timestamps = frame[TIMESTAMP_COLUMN]

    if frame.empty:
        return {
            "population": population_name,
            "rows": 0,
            "error": "No rows available",
        }

    gaps_seconds = timestamps.diff().dt.total_seconds().dropna()

    indexed = pd.Series(
        1,
        index=pd.DatetimeIndex(timestamps),
        dtype="int64",
    ).sort_index()

    rolling_5min = indexed.rolling("5min").sum()

    daily = (
        frame.assign(date=timestamps.dt.strftime("%Y-%m-%d"))
        .groupby("date")
        .size()
        .rename("rows")
        .reset_index()
    )

    active_days = len(daily)
    total_days = max(
        1,
        (timestamps.max().normalize() - timestamps.min().normalize()).days + 1,
    )

    top_days = daily.sort_values(
        "rows", ascending=False
    ).head(15)

    action_counts = (
        frame[ACTION_COLUMN]
        .fillna("<missing>")
        .value_counts()
        .head(15)
        .to_dict()
        if ACTION_COLUMN in frame.columns
        else {}
    )

    # Evaluate chronological row-based splits. These are diagnostics,
    # not a claim that any split is statistically valid.
    split_candidates = []

    for train_fraction in (0.60, 0.70, 0.80, 0.90):
        split_index = int(len(frame) * train_fraction)

        if split_index <= 0 or split_index >= len(frame):
            continue

        train = frame.iloc[:split_index]
        evaluation = frame.iloc[split_index:]

        split_candidates.append({
            "training_fraction": train_fraction,
            "training_rows": len(train),
            "evaluation_rows": len(evaluation),
            "training_start": str(train[TIMESTAMP_COLUMN].min()),
            "training_end": str(train[TIMESTAMP_COLUMN].max()),
            "evaluation_start": str(evaluation[TIMESTAMP_COLUMN].min()),
            "evaluation_end": str(evaluation[TIMESTAMP_COLUMN].max()),
            "training_active_days": int(
                train[TIMESTAMP_COLUMN].dt.normalize().nunique()
            ),
            "evaluation_active_days": int(
                evaluation[TIMESTAMP_COLUMN].dt.normalize().nunique()
            ),
            "evaluation_unique_actions": int(
                evaluation[ACTION_COLUMN].nunique()
            ) if ACTION_COLUMN in evaluation.columns else None,
            "gap_between_train_and_eval_seconds": round(
                (
                    evaluation[TIMESTAMP_COLUMN].min()
                    - train[TIMESTAMP_COLUMN].max()
                ).total_seconds(),
                4,
            ),
        })

    # Time-window diagnostics reveal whether equal-duration windows
    # contain meaningful amounts of activity.
    start = timestamps.min()
    end = timestamps.max()
    duration_seconds = (end - start).total_seconds()

    time_windows = []

    if duration_seconds > 0:
        for window_number in range(1, 5):
            lower = start + pd.Timedelta(
                seconds=duration_seconds * (window_number - 1) / 4
            )
            upper = start + pd.Timedelta(
                seconds=duration_seconds * window_number / 4
            )

            if window_number == 4:
                mask = (timestamps >= lower) & (timestamps <= upper)
            else:
                mask = (timestamps >= lower) & (timestamps < upper)

            window_frame = frame.loc[mask]

            time_windows.append({
                "window": window_number,
                "start": str(lower),
                "end": str(upper),
                "rows": len(window_frame),
                "active_days": int(
                    window_frame[TIMESTAMP_COLUMN].dt.normalize().nunique()
                ),
            })

    return {
        "population": population_name,
        "rows": len(frame),
        "start": str(start),
        "end": str(end),
        "span_days_inclusive": total_days,
        "active_days": active_days,
        "inactive_calendar_days": total_days - active_days,
        "active_day_percentage": round(
            active_days / total_days * 100, 2
        ),
        "rows_per_active_day": round(len(frame) / active_days, 2),
        "daily_count": {
            "median": percentile(daily["rows"], 0.50),
            "p90": percentile(daily["rows"], 0.90),
            "p95": percentile(daily["rows"], 0.95),
            "maximum": int(daily["rows"].max()),
        },
        "inter_event_gap_seconds": {
            "median": percentile(gaps_seconds, 0.50),
            "p90": percentile(gaps_seconds, 0.90),
            "p95": percentile(gaps_seconds, 0.95),
            "maximum": percentile(gaps_seconds, 1.00),
            "under_1_second": int((gaps_seconds < 1).sum()),
            "under_1_minute": int((gaps_seconds < 60).sum()),
            "over_1_day": int((gaps_seconds > 86400).sum()),
        },
        "maximum_rolling_5min_events": int(rolling_5min.max()),
        "top_active_days": [
            {"date": row["date"], "rows": int(row["rows"])}
            for _, row in top_days.iterrows()
        ],
        "top_actions": {
            str(key): int(value)
            for key, value in action_counts.items()
        },
        "equal_duration_windows": time_windows,
        "chronological_row_split_candidates": split_candidates,
    }


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH.resolve()}"
        )

    df = pd.read_csv(DATASET_PATH)

    required = {TIMESTAMP_COLUMN, POPULATION_COLUMN}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {sorted(missing)}"
        )

    df[TIMESTAMP_COLUMN] = pd.to_datetime(
        df[TIMESTAMP_COLUMN],
        format="mixed",
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = int(df[TIMESTAMP_COLUMN].isna().sum())
    df = df.dropna(subset=[TIMESTAMP_COLUMN]).copy()
    df = df.sort_values(TIMESTAMP_COLUMN).reset_index(drop=True)

    if df.empty:
        raise ValueError("No rows have valid timestamps.")

    df["population"] = np.where(
        df[POPULATION_COLUMN].eq(HTTP_VALUE),
        "http",
        "business",
    )

    overall_daily = (
        df.assign(
            date=df[TIMESTAMP_COLUMN].dt.strftime("%Y-%m-%d")
        )
        .groupby(["date", "population"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for column in ("http", "business"):
        if column not in overall_daily.columns:
            overall_daily[column] = 0

    overall_daily["total"] = (
        overall_daily["http"] + overall_daily["business"]
    )

    report = {
        "dataset": str(DATASET_PATH),
        "total_rows_in_file": int(len(pd.read_csv(DATASET_PATH))),
        "valid_timestamp_rows": len(df),
        "invalid_timestamp_rows": invalid_timestamps,
        "overall": {
            "start": str(df[TIMESTAMP_COLUMN].min()),
            "end": str(df[TIMESTAMP_COLUMN].max()),
            "active_days": int(
                df[TIMESTAMP_COLUMN].dt.normalize().nunique()
            ),
            "unique_timestamps": int(
                df[TIMESTAMP_COLUMN].nunique()
            ),
            "rows_with_duplicate_timestamps": int(
                df[TIMESTAMP_COLUMN].duplicated(keep=False).sum()
            ),
        },
        "populations": {},
    }

    for population_name in ("http", "business"):
        subset = df[df["population"] == population_name]
        report["populations"][population_name] = inspect_population(
            subset,
            population_name,
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DAILY_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    overall_daily.to_csv(DAILY_CSV_PATH, index=False)

    print("\n=== KBR TIMELINE INSPECTION ===")
    print(f"Dataset rows: {report['total_rows_in_file']}")
    print(f"Valid timestamps: {report['valid_timestamp_rows']}")
    print(f"Invalid timestamps: {invalid_timestamps}")
    print(f"Overall range: {report['overall']['start']} -> "
          f"{report['overall']['end']}")
    print(f"Active calendar days: {report['overall']['active_days']}")
    print(f"Duplicate-timestamp rows: "
          f"{report['overall']['rows_with_duplicate_timestamps']}")

    for name, result in report["populations"].items():
        print(f"\n--- {name.upper()} ---")
        print(f"Rows: {result['rows']}")
        print(f"Range: {result['start']} -> {result['end']}")
        print(
            f"Active days: {result['active_days']} / "
            f"{result['span_days_inclusive']} "
            f"({result['active_day_percentage']}%)"
        )
        print(
            f"Daily rows: median={result['daily_count']['median']}, "
            f"p95={result['daily_count']['p95']}, "
            f"max={result['daily_count']['maximum']}"
        )
        print(
            f"Maximum rolling 5-minute events: "
            f"{result['maximum_rolling_5min_events']}"
        )
        print("Top active days:")
        for day in result["top_active_days"][:8]:
            print(f"  {day['date']}: {day['rows']} rows")

        print("Equal-duration windows:")
        for window in result["equal_duration_windows"]:
            print(
                f"  Window {window['window']}: "
                f"{window['rows']} rows, "
                f"{window['active_days']} active days"
            )

        print("Chronological row split candidates:")
        for candidate in result["chronological_row_split_candidates"]:
            print(
                f"  {candidate['training_fraction']:.0%} train / "
                f"{1-candidate['training_fraction']:.0%} eval: "
                f"{candidate['training_rows']} / "
                f"{candidate['evaluation_rows']} rows; "
                f"{candidate['training_active_days']} / "
                f"{candidate['evaluation_active_days']} active days; "
                f"eval starts {candidate['evaluation_start']}"
            )

    print(f"\nJSON report: {REPORT_PATH.resolve()}")
    print(f"Daily CSV:   {DAILY_CSV_PATH.resolve()}")
    print("\nNo models or existing risk reports were modified.")


if __name__ == "__main__":
    main()
