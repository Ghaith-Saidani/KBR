from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/processed")


DATASETS = [
    "users.csv",
    "members.csv",
    "events.csv",
    "activities.csv",
    "news.csv",
    "user_activities.csv",
]


SENSITIVE_COLUMNS = {
    "email",
    "password",
    "password_hash",
    "phone",
    "ip_address",
    "user_agent",
    "token",
    "secret",
    "api_key",
    "authorization",
    "cookie",
}


def is_sensitive(column: str) -> bool:
    normalized = column.lower()

    return any(
        token in normalized
        for token in SENSITIVE_COLUMNS
    )


def inspect_dataset(filename: str) -> None:
    path = DATA_DIR / filename

    if not path.exists():
        print(f"\n[SKIP] {filename} - file not found")
        return

    df = pd.read_csv(path)

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    print(f"Rows:    {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")

    for column in df.columns:
        dtype = str(df[column].dtype)
        missing = int(df[column].isna().sum())
        unique = int(df[column].nunique(dropna=True))

        sensitivity = "SENSITIVE" if is_sensitive(column) else "SAFE"

        print(
            f"  - {column:<25} "
            f"dtype={dtype:<20} "
            f"missing={missing:<5} "
            f"unique={unique:<5} "
            f"[{sensitivity}]"
        )

    print("\nSample:")

    safe_columns = [
        column
        for column in df.columns
        if not is_sensitive(column)
    ]

    print(
        df[safe_columns]
        .head(3)
        .to_string(index=False)
    )


def main() -> None:
    print("=" * 70)
    print("KBR ML FEASIBILITY ANALYSIS")
    print("=" * 70)

    for dataset in DATASETS:
        inspect_dataset(dataset)

    print("\n" + "=" * 70)
    print("END")
    print("=" * 70)


if __name__ == "__main__":
    main()