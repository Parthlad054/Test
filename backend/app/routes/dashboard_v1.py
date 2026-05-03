from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import APIResponse, DashboardV1Response
from app.services import dashboard_service


router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard-v1"])


@router.get("", response_model=APIResponse[DashboardV1Response])
def get_dashboard_v1(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = dashboard_service.get_dashboard_v1(db, current_user)
    return APIResponse(status_code=200, message="Dashboard data retrieved", data=data)
