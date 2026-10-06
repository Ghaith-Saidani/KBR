from __future__ import annotations

import pandas as pd


def clean_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = dataframe.copy()

    df.columns = [
        column.strip().lower()
        for column in df.columns
    ]

    df = df.dropna(
        axis="columns",
        how="all",
    )

    # Pandas cannot hash nested Python objects such as dict/list
    # values when calculating duplicated rows. These columns are
    # valid data and must not be serialized or modified just to
    # perform duplicate detection.
    #
    # Use a temporary hashable representation only for duplicate
    # detection, while keeping the original dataframe unchanged.
    unhashable_columns = [
        column
        for column in df.columns
        if df[column].map(
            lambda value: isinstance(value, (dict, list, set))
        ).any()
    ]

    if unhashable_columns:
        duplicate_check = df.copy()

        for column in unhashable_columns:
            duplicate_check[column] = duplicate_check[column].map(
                lambda value: (
                    repr(value)
                    if isinstance(value, (dict, list, set))
                    else value
                )
            )

        duplicate_mask = duplicate_check.duplicated()
        df = df.loc[~duplicate_mask].copy()
    else:
        df = df.drop_duplicates()

    return df


def convert_datetime_columns(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    df = dataframe.copy()

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                utc=True,
            )

    return df


def prepare_events(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = clean_dataframe(dataframe)

    return convert_datetime_columns(
        df,
        [
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ],
    )


def prepare_members(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = clean_dataframe(dataframe)

    return convert_datetime_columns(
        df,
        [
            "joined_at",
            "created_at",
            "updated_at",
        ],
    )


def prepare_activities(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = clean_dataframe(dataframe)

    return convert_datetime_columns(
        df,
        [
            "created_at",
            "updated_at",
        ],
    )


def prepare_news(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = clean_dataframe(dataframe)

    return convert_datetime_columns(
        df,
        [
            "published_at",
            "created_at",
            "updated_at",
        ],
    )


def prepare_users(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = clean_dataframe(dataframe)

    return convert_datetime_columns(
        df,
        [
            "created_at",
            "updated_at",
        ],
    )


def prepare_user_activities(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    df = clean_dataframe(dataframe)

    return convert_datetime_columns(
        df,
        [
            "occurred_at",
            "created_at",
            "updated_at",
        ],
    )