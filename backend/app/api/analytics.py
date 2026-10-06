from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.analytics import (
    AnalyticsComparisonResult,
    AnalyticsDistributionResult,
    AnalyticsEngine,
    AnalyticsGrowthResult,
    AnalyticsRankingResult,
    AnalyticsResult,
    AnalyticsTrendResult,
)
from backend.app.core.database import get_db
from backend.app.core.permissions import require_admin
from backend.app.models.user import User
from backend.app.schemas.analytics import (
    AnalyticsQueryRequest,
    AnalyticsQueryResponse,
    AnalyticsResultResponse,
)

router = APIRouter(
    prefix="/admin/analytics",
    tags=["admin-analytics"],
)


@router.post(
    "/query",
    response_model=AnalyticsQueryResponse,
)
def analytics_query(
    request: AnalyticsQueryRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AnalyticsQueryResponse:
    engine = AnalyticsEngine(db)

    result = engine.analyze(request.query)

    if result is None:
        return AnalyticsQueryResponse(
            supported=False,
            result=None,
        )

    return AnalyticsQueryResponse(
        supported=True,
        result=_serialize_result(result),
    )


def _serialize_result(
    result: (
        AnalyticsResult
        | AnalyticsTrendResult
        | AnalyticsComparisonResult
        | AnalyticsDistributionResult
        | AnalyticsGrowthResult
        | AnalyticsRankingResult
    ),
) -> AnalyticsResultResponse:

    if isinstance(result, AnalyticsComparisonResult):
        return AnalyticsResultResponse(
            type="comparison",
            metric=result.metric,
            label=result.label,
            source=result.source,
            first_period_label=result.first_period_label,
            first_value=result.first_value,
            second_period_label=result.second_period_label,
            second_value=result.second_value,
            difference=result.difference,
            percentage_change=result.percentage_change,
        )

    if isinstance(result, AnalyticsTrendResult):
        return AnalyticsResultResponse(
            type="trend",
            metric=result.metric,
            label=result.label,
            source=result.source,
            start_date=result.start_date,
            end_date=result.end_date,
            months=result.months,
        )

    if isinstance(result, AnalyticsDistributionResult):
        return AnalyticsResultResponse(
            type="distribution",
            metric=result.metric,
            label=result.label,
            source=result.source,
            categories=result.categories,
        )

    if isinstance(result, AnalyticsGrowthResult):
        return AnalyticsResultResponse(
            type="growth",
            metric=result.metric,
            label=result.label,
            source=result.source,
            current_period_label=result.current_period_label,
            current_value=result.current_value,
            previous_period_label=result.previous_period_label,
            previous_value=result.previous_value,
            difference=result.difference,
            percentage_change=result.percentage_change,
            direction=result.direction,
        )

    if isinstance(result, AnalyticsRankingResult):
        return AnalyticsResultResponse(
            type="ranking",
            metric=result.metric,
            label=result.label,
            source=result.source,
            period_label=result.period_label,
            rank=result.rank,
            value=result.value,
            direction=result.direction,
        )

    return AnalyticsResultResponse(
        type="metric",
        metric=result.metric,
        value=result.value,
        label=result.label,
        source=result.source,
        start_date=result.start_date,
        end_date=result.end_date,
    )


__all__ = [
    "router",
]