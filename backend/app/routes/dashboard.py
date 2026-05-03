from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import DashboardResponse, APIResponse
from app.dependencies import get_current_user
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("", response_model=APIResponse[DashboardResponse])
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stats = dashboard_service.get_dashboard_stats(db, current_user)
    return APIResponse(status_code=200, message="Dashboard stats retrieved", data=stats)
