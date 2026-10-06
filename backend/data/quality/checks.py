from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass
class QualityResult:
    dataset: str
    rows: int
    columns: int
    duplicate_rows: int
    missing_values: int
    missing_cells_percentage: float
    passed: bool


def _duplicate_count(
    dataframe: pd.DataFrame,
) -> int:
    """
    Calculate duplicate rows safely, including DataFrames
    containing nested Python objects such as dictionaries,
    lists, or sets.
    """

    unhashable_columns = [
        column
        for column in dataframe.columns
        if dataframe[column].map(
            lambda value: isinstance(
                value,
                (dict, list, set),
            )
        ).any()
    ]

    if not unhashable_columns:
        return int(
            dataframe.duplicated().sum()
        )

    duplicate_check = dataframe.copy()

    for column in unhashable_columns:
        duplicate_check[column] = duplicate_check[
            column
        ].map(
            lambda value: (
                repr(value)
                if isinstance(
                    value,
                    (dict, list, set),
                )
                else value
            )
        )

    return int(
        duplicate_check.duplicated().sum()
    )


def check_dataframe(
    dataframe: pd.DataFrame,
    dataset_name: str,
) -> QualityResult:
    rows = len(dataframe)
    columns = len(dataframe.columns)

    duplicate_rows = _duplicate_count(
        dataframe
    )

    missing_values = int(
        dataframe.isna().sum().sum()
    )

    total_cells = rows * columns

    missing_percentage = (
        (missing_values / total_cells) * 100
        if total_cells > 0
        else 0.0
    )

    passed = duplicate_rows == 0

    return QualityResult(
        dataset=dataset_name,
        rows=rows,
        columns=columns,
        duplicate_rows=duplicate_rows,
        missing_values=missing_values,
        missing_cells_percentage=round(
            missing_percentage,
            2,
        ),
        passed=passed,
    )


def run_quality_checks(
    datasets: dict[str, pd.DataFrame],
) -> list[QualityResult]:
    results: list[QualityResult] = []

    print("\n" + "=" * 60)
    print("DATA QUALITY")
    print("=" * 60)

    for name, dataframe in datasets.items():
        result = check_dataframe(
            dataframe,
            name,
        )

        results.append(result)

        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        print(
            f"[QUALITY] {name}: {status} | "
            f"rows={result.rows} | "
            f"columns={result.columns} | "
            f"duplicates={result.duplicate_rows} | "
            f"missing={result.missing_values} "
            f"({result.missing_cells_percentage}%)"
        )

    return results


def quality_results_to_dataframe(
    results: list[QualityResult],
) -> pd.DataFrame:
    return pd.DataFrame(
        [asdict(result) for result in results]
    )