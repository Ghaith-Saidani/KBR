from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def extract_table(
    engine: Engine,
    table_name: str,
) -> pd.DataFrame:
    allowed_tables = {
        "users",
        "members",
        "events",
        "activities",
        "news",
        "user_activities",
    }

    if table_name not in allowed_tables:
        raise ValueError(
            f"Unsupported table: {table_name}"
        )

    query = text(
        f'SELECT * FROM "{table_name}"'
    )

    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def extract_kbr_data(
    database_url: str,
    output_dir: Path,
) -> dict[str, pd.DataFrame]:
    engine = get_engine(database_url)

    tables = [
        "users",
        "members",
        "events",
        "activities",
        "news",
        "user_activities",
    ]

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    datasets: dict[str, pd.DataFrame] = {}

    for table in tables:
        try:
            dataframe = extract_table(
                engine,
                table,
            )

            datasets[table] = dataframe

            dataframe.to_csv(
                output_dir / f"{table}.csv",
                index=False,
            )

            print(
                f"[EXTRACT] {table}: "
                f"{len(dataframe)} rows"
            )

        except Exception as exc:
            print(
                f"[WARNING] Could not extract "
                f"{table}: {exc}"
            )

    return datasets
