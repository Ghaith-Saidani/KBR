from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class AnalyticsQueryRequest(BaseModel):
    query: str


class AnalyticsResultResponse(BaseModel):
    type: Literal[
        "metric",
        "trend",
        "comparison",
        "distribution",
        "growth",
        "ranking",
    ]

    metric: str
    value: int | None = None
    label: str
    source: str

    start_date: date | None = None
    end_date: date | None = None

    months: list[tuple[str, int]] | None = None

    first_period_label: str | None = None
    first_value: int | None = None

    second_period_label: str | None = None
    second_value: int | None = None

    difference: int | None = None
    percentage_change: float | None = None

    categories: list[tuple[str, int]] | None = None

    current_period_label: str | None = None
    current_value: int | None = None

    previous_period_label: str | None = None
    previous_value: int | None = None

    direction: str | None = None

    period_label: str | None = None
    rank: int | None = None


class AnalyticsQueryResponse(BaseModel):
    supported: bool
    result: AnalyticsResultResponse | None = None