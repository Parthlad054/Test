from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, RoleEnum
from app.schemas.schemas import APIResponse, UserCreate, UserLogin, UserResponse, AuthTokens
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user


router = APIRouter(prefix="/api/v1/auth", tags=["auth-v1"])


def _build_auth_response(user: User) -> AuthTokens:
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": getattr(user.role, "value", user.role)}
    )
    return AuthTokens(access_token=access_token, token_type="bearer", user=user)


@router.post("/signup", response_model=APIResponse[AuthTokens])
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    first_user = db.query(User).count() == 0
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=RoleEnum.admin if first_user else RoleEnum.member,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return APIResponse(status_code=200, message="Signup successful", data=_build_auth_response(user))


@router.post("/login", response_model=APIResponse[AuthTokens])
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")
    return APIResponse(status_code=200, message="Login successful", data=_build_auth_response(user))


@router.get("/me", response_model=APIResponse[UserResponse])
def me(current_user: User = Depends(get_current_user)):
    return APIResponse(status_code=200, message="Current user retrieved", data=current_user)
