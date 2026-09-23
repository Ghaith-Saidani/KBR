from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.permissions import require_admin
from backend.app.models.user import User
from backend.app.schemas.statistics import (
    RecentBusinessActivityResponse,
    StatisticsOverviewResponse,
    StatisticsTrendsResponse,
)
from backend.app.services.statistics import (
    get_recent_business_activity,
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


@router.get(
    "/recent-activity",
    response_model=RecentBusinessActivityResponse,
)
def recent_business_activity(
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of recent business activities to return.",
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RecentBusinessActivityResponse:
    """
    Return recent semantic business activity for the admin dashboard.
    """

    return get_recent_business_activity(
        db,
        limit=limit,
    )