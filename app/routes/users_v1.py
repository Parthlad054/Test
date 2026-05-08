from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import APIResponse, UserResponse, UserListResponse
from app.dependencies import get_current_admin_user, get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users-v1"])


@router.get("", response_model=APIResponse[UserListResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(func.count(User.id)).scalar() or 0
    return APIResponse(status_code=200, message="Users retrieved", data={"users": users, "total": int(total)})


@router.get("/{user_id}", response_model=APIResponse[UserResponse])
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return APIResponse(status_code=200, message="User retrieved", data=user)
