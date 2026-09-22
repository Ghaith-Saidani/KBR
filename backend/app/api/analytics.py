from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.analytics import (
    AnalyticsComparisonResult,
    AnalyticsEngine,
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
    engine = AnalyticsEngine(
        db,
    )

    result = engine.analyze(
        request.query,
    )

    if result is None:
        return AnalyticsQueryResponse(
            supported=False,
            result=None,
        )

    return AnalyticsQueryResponse(
        supported=True,
        result=_serialize_result(
            result,
        ),
    )


def _serialize_result(
    result: (
        AnalyticsResult
        | AnalyticsTrendResult
        | AnalyticsComparisonResult
    ),
) -> AnalyticsResultResponse:
    if isinstance(
        result,
        AnalyticsComparisonResult,
    ):
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

    if isinstance(
        result,
        AnalyticsTrendResult,
    ):
        return AnalyticsResultResponse(
            type="trend",
            metric=result.metric,
            label=result.label,
            source=result.source,
            start_date=result.start_date,
            end_date=result.end_date,
            months=result.months,
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