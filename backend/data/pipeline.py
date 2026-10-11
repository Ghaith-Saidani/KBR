from __future__ import annotations

import json
from pathlib import Path

from backend.app.core.config import Settings
from backend.data.extract.postgres import (
    extract_kbr_data,
)
from backend.data.profile.profiler import (
    profile_datasets,
)
from backend.data.quality.checks import (
    quality_results_to_dataframe,
    run_quality_checks,
)
from backend.data.transform.datasets import (
    prepare_activities,
    prepare_events,
    prepare_members,
    prepare_news,
    prepare_user_activities,
    prepare_users,
)


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"

PROCESSED_DIR = DATA_DIR / "processed"

REPORTS_DIR = DATA_DIR / "reports"


TRANSFORMERS = {
    "users": prepare_users,
    "members": prepare_members,
    "events": prepare_events,
    "activities": prepare_activities,
    "news": prepare_news,
    "user_activities": prepare_user_activities,
}


def run_pipeline() -> None:
    settings = Settings()
    database_url = settings.database_url

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 60)
    print("KBR DATA PIPELINE")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. EXTRACTION
    # --------------------------------------------------------

    print("\n[1/4] Extracting PostgreSQL data...")

    datasets = extract_kbr_data(
        database_url,
        RAW_DIR,
    )

    if not datasets:
        raise RuntimeError(
            "No datasets were extracted."
        )

    # --------------------------------------------------------
    # 2. TRANSFORMATION
    # --------------------------------------------------------

    print("\n[2/4] Transforming datasets...")

    processed_datasets = {}

    for name, dataframe in datasets.items():
        transformer = TRANSFORMERS.get(name)

        if transformer is None:
            continue

        processed = transformer(
            dataframe
        )

        processed_datasets[name] = processed

        processed.to_csv(
            PROCESSED_DIR / f"{name}.csv",
            index=False,
        )

        print(
            f"[TRANSFORM] {name}: "
            f"{len(processed)} rows"
        )

    # --------------------------------------------------------
    # 3. DATA QUALITY
    # --------------------------------------------------------

    print("\n[3/4] Running data-quality checks...")

    quality_results = run_quality_checks(
        processed_datasets
    )

    quality_report = quality_results_to_dataframe(
        quality_results
    )

    quality_report.to_csv(
        REPORTS_DIR / "data_quality.csv",
        index=False,
    )

    failed = [
        result
        for result in quality_results
        if not result.passed
    ]

    # --------------------------------------------------------
    # 4. DATASET PROFILING
    # --------------------------------------------------------

    print("\n[4/4] Profiling datasets...")

    profiles = profile_datasets(
        processed_datasets
    )

    profile_path = (
        REPORTS_DIR / "data_profile.json"
    )

    with profile_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            profiles,
            file,
            indent=2,
            ensure_ascii=False,
        )

    for name, profile in profiles.items():
        print(
            f"[PROFILE] {name}: "
            f"{profile['rows']} rows | "
            f"{profile['columns']} columns | "
            f"missing={profile['missing_percentage']}%"
        )

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    if failed:
        print(
            f"PIPELINE COMPLETED WITH "
            f"{len(failed)} QUALITY FAILURE(S)"
        )
    else:
        print(
            "PIPELINE COMPLETED SUCCESSFULLY"
        )

    print("=" * 60)

    print(
        f"\nProfile report: {profile_path}"
    )


if __name__ == "__main__":
    run_pipeline()