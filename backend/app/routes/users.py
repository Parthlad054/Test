from fastapi import APIRouter, Depends
from app.schemas.schemas import UserResponse, APIResponse
from app.models.models import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=APIResponse[UserResponse])
def read_users_me(current_user: User = Depends(get_current_user)):
    return APIResponse(status_code=200, message="User retrieved successfully", data=current_user)
