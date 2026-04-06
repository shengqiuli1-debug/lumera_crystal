from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.admin_dashboard_repository import AdminDashboardRepository
from app.schemas.admin_dashboard import DashboardOverviewResponse
from app.services.admin_dashboard_service import AdminDashboardService

router = APIRouter(prefix="/dashboard", tags=["admin-dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> DashboardOverviewResponse:
    service = AdminDashboardService(AdminDashboardRepository(db))
    return service.get_overview()
