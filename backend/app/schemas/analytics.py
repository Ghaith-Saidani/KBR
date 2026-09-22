from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class AnalyticsQueryRequest(BaseModel):
    query: str


class AnalyticsResultResponse(BaseModel):
    type: str
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


class AnalyticsQueryResponse(BaseModel):
    supported: bool
    result: AnalyticsResultResponse | None = None