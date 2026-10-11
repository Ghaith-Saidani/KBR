from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd


# Only these low-risk categorical fields may expose
# their most frequent values in the profiling report.
SAFE_CATEGORICAL_COLUMNS = {
    "role",
    "status",
    "method",
    "resource_type",
}


SENSITIVE_COLUMN_TOKENS = {
    "password",
    "password_hash",
    "email",
    "phone",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "user_agent",
    "ip_address",
}


def _is_sensitive_column(column: str) -> bool:
    normalized = column.strip().lower()

    return any(
        token in normalized
        for token in SENSITIVE_COLUMN_TOKENS
    )


def _is_nested_value(value: Any) -> bool:
    return isinstance(
        value,
        (dict, list, set, tuple),
    )


def _safe_json_value(value: Any) -> Any:
    """
    Convert pandas/Python values into JSON-serializable values.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and pd.isna(value):
            return None
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _safe_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _safe_json_value(item)
            for item in value
        ]

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return str(value)


def _column_profile(
    dataframe: pd.DataFrame,
    column: str,
) -> dict[str, Any]:
    series = dataframe[column]

    missing_count = int(
        series.isna().sum()
    )

    nested_values = bool(
        series.map(_is_nested_value).any()
    )

    profile: dict[str, Any] = {
        "name": column,
        "dtype": str(series.dtype),
        "rows": int(len(series)),
        "missing": missing_count,
        "missing_percentage": round(
            (
                missing_count / len(series) * 100
                if len(series) > 0
                else 0.0
            ),
            2,
        ),
        "unique": (
            int(series.nunique(dropna=True))
            if not nested_values
            else None
        ),
        "nested_values": nested_values,
        "sensitive": _is_sensitive_column(column),
    }

    non_null = series.dropna()

    if non_null.empty:
        return profile

    # --------------------------------------------------------
    # Numeric statistics
    # --------------------------------------------------------

    if pd.api.types.is_numeric_dtype(series):
        profile["statistics"] = {
            "min": _safe_json_value(
                series.min()
            ),
            "max": _safe_json_value(
                series.max()
            ),
            "mean": _safe_json_value(
                series.mean()
            ),
            "median": _safe_json_value(
                series.median()
            ),
        }

        return profile

    # --------------------------------------------------------
    # Datetime statistics
    # --------------------------------------------------------

    if pd.api.types.is_datetime64_any_dtype(
        series
    ):
        profile["statistics"] = {
            "min": _safe_json_value(
                series.min()
            ),
            "max": _safe_json_value(
                series.max()
            ),
        }

        return profile

    # --------------------------------------------------------
    # Categorical statistics
    # --------------------------------------------------------

    if (
        column in SAFE_CATEGORICAL_COLUMNS
        and not nested_values
        and not _is_sensitive_column(column)
    ):
        profile["top_values"] = [
            {
                "value": _safe_json_value(value),
                "count": int(count),
            }
            for value, count in (
                series.value_counts(
                    dropna=True
                )
                .head(10)
                .items()
            )
        ]

    return profile


def profile_dataframe(
    dataframe: pd.DataFrame,
    dataset_name: str,
) -> dict[str, Any]:
    """
    Generate a privacy-safe structural and
    statistical profile for a dataset.

    The profiler never exports raw values from
    arbitrary columns.
    """

    rows = int(len(dataframe))
    columns = int(len(dataframe.columns))

    missing_values = int(
        dataframe.isna().sum().sum()
    )

    total_cells = rows * columns

    missing_percentage = (
        (
            missing_values
            / total_cells
            * 100
        )
        if total_cells > 0
        else 0.0
    )

    nested_columns = [
        column
        for column in dataframe.columns
        if dataframe[column].map(
            _is_nested_value
        ).any()
    ]

    sensitive_columns = [
        column
        for column in dataframe.columns
        if _is_sensitive_column(column)
    ]

    return {
        "dataset": dataset_name,
        "rows": rows,
        "columns": columns,
        "missing_values": missing_values,
        "missing_percentage": round(
            missing_percentage,
            2,
        ),
        "nested_columns": nested_columns,
        "sensitive_columns": sensitive_columns,
        "column_profiles": [
            _column_profile(
                dataframe,
                column,
            )
            for column in dataframe.columns
        ],
    }


def profile_datasets(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """
    Generate privacy-safe profiles for all
    processed datasets.
    """

    return {
        name: profile_dataframe(
            dataframe,
            name,
        )
        for name, dataframe in datasets.items()
    }