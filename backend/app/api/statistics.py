from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.permissions import require_admin
from backend.app.models.user import User
from backend.app.schemas.statistics import (
    StatisticsOverviewResponse,
    StatisticsTrendsResponse,
)
from backend.app.services.statistics import (
    get_statistics_overview,
    get_statistics_trends,
)


router = APIRouter(
    prefix="/admin/statistics",
    tags=["admin-statistics"],
)


@router.get(
    "/overview",
    response_model=StatisticsOverviewResponse,
)
def statistics_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> StatisticsOverviewResponse:
    """
    Return global KBR statistics.
    """

    return get_statistics_overview(db)


@router.get(
    "/trends",
    response_model=StatisticsTrendsResponse,
)
def statistics_trends(
    months: int = Query(
        default=6,
        ge=1,
        le=24,
        description="Number of months to include.",
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> StatisticsTrendsResponse:
    """
    Return monthly KBR statistics.
    """

    return get_statistics_trends(
        db,
        months=months,
    )