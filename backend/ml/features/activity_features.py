from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd


DATA_PATH = Path("data/processed/user_activities.csv")


def load_activity_data(
    path: Path = DATA_PATH,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Activity dataset not found: {path}"
        )

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError("Activity dataset is empty.")

    required_columns = {
        "id",
        "user_id",
        "action",
        "resource_type",
        "method",
        "endpoint",
        "details",
        "activity_metadata",
        "occurred_at",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    return df


def extract_status_code(details: object) -> int:
    if not isinstance(details, str):
        return 0

    text = details.strip()

    if not text.startswith("HTTP "):
        return 0

    parts = text.split()

    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])

    return 0


def extract_query_parameter_count(
    metadata: object,
) -> int:
    if not isinstance(metadata, str):
        return 0

    try:
        parsed = ast.literal_eval(metadata)
    except (ValueError, SyntaxError):
        return 0

    if not isinstance(parsed, dict):
        return 0

    query_params = parsed.get("query_params")

    if not isinstance(query_params, dict):
        return 0

    return len(query_params)


def normalize_endpoint(endpoint: object) -> str:
    if not isinstance(endpoint, str):
        return "unknown"

    endpoint = endpoint.strip()

    if not endpoint:
        return "unknown"

    return endpoint.split("?", maxsplit=1)[0]


def _add_population_rolling_counts(
    work: pd.DataFrame,
    population_mask: pd.Series,
    prefix: str,
) -> None:
    """
    Add historical population-level activity counts.

    Counts are calculated only from rows belonging to the same
    population as the current row and exclude the current activity.
    """

    population = (
        work.loc[population_mask]
        .sort_values("occurred_at")
        .copy()
    )

    if population.empty:
        work[f"{prefix}_count_5m"] = 0
        work[f"{prefix}_count_1h"] = 0
        work[f"{prefix}_count_24h"] = 0
        return

    activity_series = pd.Series(
        1,
        index=pd.DatetimeIndex(
            population["occurred_at"]
        ),
        dtype="int64",
    )

    historical_activity = activity_series.shift(1)

    counts_5m = (
        historical_activity
        .rolling(
            "5min",
            min_periods=1,
        )
        .sum()
        .fillna(0)
        .to_numpy()
    )

    counts_1h = (
        historical_activity
        .rolling(
            "1h",
            min_periods=1,
        )
        .sum()
        .fillna(0)
        .to_numpy()
    )

    counts_24h = (
        historical_activity
        .rolling(
            "24h",
            min_periods=1,
        )
        .sum()
        .fillna(0)
        .to_numpy()
    )

    work.loc[
        population.index,
        f"{prefix}_count_5m",
    ] = counts_5m

    work.loc[
        population.index,
        f"{prefix}_count_1h",
    ] = counts_1h

    work.loc[
        population.index,
        f"{prefix}_count_24h",
    ] = counts_24h


def _add_population_user_rolling_counts(
    work: pd.DataFrame,
    population_mask: pd.Series,
    prefix: str,
) -> None:
    """
    Add historical per-user activity counts inside one population.

    Anonymous activities are grouped under the same anonymous key.
    The current activity is excluded from all rolling counts.
    """

    work[f"{prefix}_user_activity_count_1h"] = 0
    work[f"{prefix}_user_activity_count_24h"] = 0

    population = (
        work.loc[population_mask]
        .sort_values("occurred_at")
        .copy()
    )

    if population.empty:
        return

    population["_user_key"] = (
        population["user_id"]
        .fillna("anonymous")
        .astype(str)
    )

    count_1h = pd.Series(
        0,
        index=population.index,
        dtype="int64",
    )

    count_24h = pd.Series(
        0,
        index=population.index,
        dtype="int64",
    )

    for _, group in population.groupby(
        "_user_key",
        sort=False,
    ):
        user_series = pd.Series(
            1,
            index=pd.DatetimeIndex(
                group["occurred_at"]
            ),
            dtype="int64",
        )

        historical_user = user_series.shift(1)

        counts_1h = (
            historical_user
            .rolling(
                "1h",
                min_periods=1,
            )
            .sum()
            .fillna(0)
            .astype(int)
            .to_numpy()
        )

        counts_24h = (
            historical_user
            .rolling(
                "24h",
                min_periods=1,
            )
            .sum()
            .fillna(0)
            .astype(int)
            .to_numpy()
        )

        count_1h.loc[group.index] = counts_1h
        count_24h.loc[group.index] = counts_24h

    work.loc[
        population.index,
        f"{prefix}_user_activity_count_1h",
    ] = count_1h.to_numpy()

    work.loc[
        population.index,
        f"{prefix}_user_activity_count_24h",
    ] = count_24h.to_numpy()


def add_temporal_features(
    work: pd.DataFrame,
) -> pd.DataFrame:
    work = (
        work.sort_values("occurred_at")
        .reset_index(drop=True)
        .copy()
    )

    work["hour"] = work["occurred_at"].dt.hour

    work["day_of_week"] = (
        work["occurred_at"].dt.dayofweek
    )

    work["is_weekend"] = (
        work["day_of_week"] >= 5
    ).astype(int)

    # --------------------------------------------------------------
    # Population-aware historical activity
    #
    # HTTP and business activities are deliberately separated.
    # This prevents a burst of HTTP requests from influencing
    # business-event anomaly detection and vice versa.
    # --------------------------------------------------------------

    http_mask = work["is_http_request"].eq(1)
    business_mask = ~http_mask

    _add_population_rolling_counts(
        work,
        http_mask,
        "http_activity",
    )

    _add_population_rolling_counts(
        work,
        business_mask,
        "business_activity",
    )

    _add_population_user_rolling_counts(
        work,
        http_mask,
        "http",
    )

    _add_population_user_rolling_counts(
        work,
        business_mask,
        "business",
    )

    # --------------------------------------------------------------
    # Unified model-facing temporal features
    #
    # Each row receives counts from its own population only.
    # --------------------------------------------------------------

    work["activity_count_5m"] = np.where(
        http_mask,
        work["http_activity_count_5m"],
        work["business_activity_count_5m"],
    )

    work["activity_count_1h"] = np.where(
        http_mask,
        work["http_activity_count_1h"],
        work["business_activity_count_1h"],
    )

    work["activity_count_24h"] = np.where(
        http_mask,
        work["http_activity_count_24h"],
        work["business_activity_count_24h"],
    )

    work["user_activity_count_1h"] = np.where(
        http_mask,
        work["http_user_activity_count_1h"],
        work["business_user_activity_count_1h"],
    )

    work["user_activity_count_24h"] = np.where(
        http_mask,
        work["http_user_activity_count_24h"],
        work["business_user_activity_count_24h"],
    )

    # --------------------------------------------------------------
    # Time since previous activity
    #
    # Also population-aware: HTTP rows are compared against the
    # previous HTTP activity; business rows against business
    # activity.
    # --------------------------------------------------------------

    previous_activity_time = pd.Series(
        pd.NaT,
        index=work.index,
        dtype="datetime64[ns, UTC]",
    )

    for population_mask in (
        http_mask,
        business_mask,
    ):
        population = (
            work.loc[population_mask]
            .sort_values("occurred_at")
        )

        previous_activity_time.loc[
            population.index
        ] = population["occurred_at"].shift(1)

    work["time_since_previous_activity_seconds"] = (
        work["occurred_at"]
        .sub(previous_activity_time)
        .dt.total_seconds()
        .fillna(0)
        .clip(lower=0)
    )

    work["log_time_since_previous_activity"] = (
        np.log1p(
            work[
                "time_since_previous_activity_seconds"
            ]
        )
    )

    return work


def add_categorical_features(
    work: pd.DataFrame,
) -> pd.DataFrame:
    work["action"] = (
        work["action"]
        .fillna("UNKNOWN")
        .astype(str)
    )

    work["resource_type"] = (
        work["resource_type"]
        .fillna("UNKNOWN")
        .astype(str)
    )

    work["method"] = (
        work["method"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    work["endpoint_normalized"] = (
        work["endpoint"]
        .apply(normalize_endpoint)
    )

    return work


def add_http_features(
    work: pd.DataFrame,
) -> pd.DataFrame:
    work["status_code"] = (
        work["details"]
        .apply(extract_status_code)
    )

    work["is_http_request"] = (
        work["resource_type"]
        .eq("http_request")
    ).astype(int)

    work["query_parameter_count"] = (
        work["activity_metadata"]
        .apply(extract_query_parameter_count)
    )

    work["is_error_status"] = (
        work["status_code"]
        .between(400, 599)
    ).astype(int)

    work["is_auth_failure"] = (
        work["status_code"]
        .isin([401, 403])
    ).astype(int)

    return work


def build_activity_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    work = df.copy()

    work["occurred_at"] = pd.to_datetime(
        work["occurred_at"],
        errors="coerce",
        utc=True,
        format="mixed",
    )

    invalid_timestamps = int(
        work["occurred_at"].isna().sum()
    )

    if invalid_timestamps:
        raise ValueError(
            "Activity dataset contains "
            f"{invalid_timestamps} invalid timestamps."
        )

    work = add_http_features(work)
    work = add_temporal_features(work)
    work = add_categorical_features(work)

    feature_columns = [
        # Metadata
        "id",
        "occurred_at",

        # Population
        "is_http_request",

        # Categorical features
        "action",
        "resource_type",
        "method",
        "endpoint_normalized",

        # Calendar features
        "hour",
        "day_of_week",
        "is_weekend",

        # HTTP features
        "status_code",
        "is_error_status",
        "is_auth_failure",
        "query_parameter_count",

        # Population-aware temporal behavior
        "activity_count_5m",
        "activity_count_1h",
        "activity_count_24h",
        "time_since_previous_activity_seconds",
        "log_time_since_previous_activity",

        # Population-aware user behavior
        "user_activity_count_1h",
        "user_activity_count_24h",
    ]

    features = work[feature_columns].copy()

    numeric_columns = [
        "is_http_request",
        "hour",
        "day_of_week",
        "is_weekend",
        "status_code",
        "is_error_status",
        "is_auth_failure",
        "query_parameter_count",
        "activity_count_5m",
        "activity_count_1h",
        "activity_count_24h",
        "time_since_previous_activity_seconds",
        "log_time_since_previous_activity",
        "user_activity_count_1h",
        "user_activity_count_24h",
    ]

    features[numeric_columns] = (
        features[numeric_columns]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

    categorical_columns = [
        "action",
        "resource_type",
        "method",
        "endpoint_normalized",
    ]

    features[categorical_columns] = (
        features[categorical_columns]
        .fillna("UNKNOWN")
        .astype(str)
    )

    return features


def build_activity_feature_dataset(
    path: Path = DATA_PATH,
) -> pd.DataFrame:
    raw = load_activity_data(path)

    return build_activity_features(raw)


def print_feature_summary(
    features: pd.DataFrame,
) -> None:
    print("=" * 70)
    print("KBR ACTIVITY ML FEATURE DATASET")
    print("=" * 70)

    print(f"Rows:    {len(features)}")
    print(f"Columns: {len(features.columns)}")

    print("\nColumns:")

    for column in features.columns:
        print(f"  - {column}")

    print("\nHTTP vs business activities:")

    print(
        features["is_http_request"]
        .value_counts()
        .rename(
            index={
                0: "business",
                1: "http_request",
            }
        )
        .to_string()
    )

    print("\nStatus codes:")

    print(
        features["status_code"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nError status distribution:")

    print(
        features["is_error_status"]
        .value_counts()
        .rename(
            index={
                0: "non_error",
                1: "error",
            }
        )
        .to_string()
    )

    print("\nTemporal feature summary:")

    temporal_columns = [
        "activity_count_5m",
        "activity_count_1h",
        "activity_count_24h",
        "time_since_previous_activity_seconds",
        "log_time_since_previous_activity",
        "user_activity_count_1h",
        "user_activity_count_24h",
    ]

    print(
        features[temporal_columns]
        .describe()
        .round(2)
        .to_string()
    )

    print("\nCategorical cardinality:")

    categorical_columns = [
        "action",
        "resource_type",
        "method",
        "endpoint_normalized",
    ]

    for column in categorical_columns:
        print(
            f"  - {column}: "
            f"{features[column].nunique()} unique"
        )

    print("\nMissing values:")

    print(
        features.isna()
        .sum()
        .to_string()
    )

    print("\nFeature preview:")

    print(
        features.head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    feature_dataset = (
        build_activity_feature_dataset()
    )

    print_feature_summary(
        feature_dataset
    )