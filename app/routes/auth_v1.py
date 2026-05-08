from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, RoleEnum
from app.schemas.schemas import APIResponse, UserCreate, UserLogin, UserResponse, AuthTokens
from app.dependencies import get_current_user
from app.services import auth_service


router = APIRouter(prefix="/api/v1/auth", tags=["auth-v1"])


@router.post("/signup", response_model=APIResponse[AuthTokens])
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    first_user = db.query(User).count() == 0
    user = auth_service.register_user(
        payload,
        db,
        RoleEnum.admin if first_user else RoleEnum.employee,
    )
    return APIResponse(status_code=200, message="Signup successful", data=auth_service.create_auth_tokens(user))


@router.post("/login", response_model=APIResponse[AuthTokens])
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(payload, db)
    return APIResponse(status_code=200, message="Login successful", data=auth_service.create_auth_tokens(user))


@router.get("/me", response_model=APIResponse[UserResponse])
def me(current_user: User = Depends(get_current_user)):
    return APIResponse(status_code=200, message="Current user retrieved", data=current_user)
