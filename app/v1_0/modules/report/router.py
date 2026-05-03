from fastapi import APIRouter, Depends, status
from dependency_injector.wiring import Provide, inject

from app.infraestructure.models.user import User, GlobalRole
from app.middlewares import require_roles
from .dto.schemas import DashboardReportDTO
from .service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

_allowed_roles = Depends(require_roles(GlobalRole.USER, GlobalRole.ADMIN))


@router.get(
    "/dashboard",
    response_model=DashboardReportDTO,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics",
    description=(
        "Returns aggregated metrics for the dashboard: total customers, products, "
        "warehouses, seaports, shipments by status, total revenue, top destinations, "
        "and the 5 most recent shipments."
    ),
)
@inject
async def get_dashboard_stats(
    _current_user: User = _allowed_roles,
    report_service: ReportService = Depends(Provide["report_service"]),
) -> DashboardReportDTO:
    return await report_service.get_dashboard_stats()
