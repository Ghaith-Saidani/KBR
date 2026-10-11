from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.permissions import require_admin
from backend.app.models.user import User
from backend.app.schemas.ml_risk import (
    MLRiskConfigurationResponse,
    MLRiskHealthResponse,
    MLRiskIncidentsResponse,
    MLRiskObservationsResponse,
    MLRiskSummaryResponse,
)
from backend.app.services.ml_risk import (
    MLRiskReportInvalidError,
    MLRiskReportNotFoundError,
    REPORT_PATH,
    get_risk_configuration,
    get_risk_summary,
    get_top_incidents,
    get_top_risks,
    load_risk_report,
)

router = APIRouter(
    prefix="/admin/ml/risk",
    tags=["admin-ml-risk"],
)


def _raise_report_error(exc: Exception) -> HTTPException:
    if isinstance(exc, MLRiskReportNotFoundError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Risk-scoring report is unavailable. "
                "Run `python -m backend.ml.risk_scoring` first."
            ),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Risk-scoring report is invalid or could not be loaded.",
    )


@router.get("/summary", response_model=MLRiskSummaryResponse)
def risk_summary(
    current_user: User = Depends(require_admin),
) -> MLRiskSummaryResponse:
    try:
        return MLRiskSummaryResponse(**get_risk_summary())
    except (MLRiskReportNotFoundError, MLRiskReportInvalidError) as exc:
        raise _raise_report_error(exc) from exc


@router.get("/observations", response_model=MLRiskObservationsResponse)
def risk_observations(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
) -> MLRiskObservationsResponse:
    try:
        items = get_top_risks(limit=limit)
        return MLRiskObservationsResponse(items=items, count=len(items))
    except (MLRiskReportNotFoundError, MLRiskReportInvalidError) as exc:
        raise _raise_report_error(exc) from exc


@router.get("/incidents", response_model=MLRiskIncidentsResponse)
def risk_incidents(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
) -> MLRiskIncidentsResponse:
    try:
        items = get_top_incidents(limit=limit)
        return MLRiskIncidentsResponse(items=items, count=len(items))
    except (MLRiskReportNotFoundError, MLRiskReportInvalidError) as exc:
        raise _raise_report_error(exc) from exc


@router.get("/configuration", response_model=MLRiskConfigurationResponse)
def risk_configuration(
    current_user: User = Depends(require_admin),
) -> MLRiskConfigurationResponse:
    try:
        return MLRiskConfigurationResponse(**get_risk_configuration())
    except (MLRiskReportNotFoundError, MLRiskReportInvalidError) as exc:
        raise _raise_report_error(exc) from exc


@router.get("/health", response_model=MLRiskHealthResponse)
def risk_health(
    current_user: User = Depends(require_admin),
) -> MLRiskHealthResponse:
    try:
        load_risk_report()
        return MLRiskHealthResponse(
            available=True,
            report_path=str(REPORT_PATH),
            message="Risk-scoring report is available.",
        )
    except MLRiskReportNotFoundError:
        return MLRiskHealthResponse(
            available=False,
            report_path=str(REPORT_PATH),
            message="Risk-scoring report has not been generated.",
        )
    except MLRiskReportInvalidError:
        return MLRiskHealthResponse(
            available=False,
            report_path=str(REPORT_PATH),
            message="Risk-scoring report is invalid or unreadable.",
        )


__all__ = ["router"]
