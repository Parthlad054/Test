from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import UserCreate, UserLogin, Token, TokenRefresh, UserResponse, APIResponse, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordWithOTPRequest
from app.services import auth_service
from jose import jwt, JWTError
from app.core.config import settings
from app.models.models import User
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=APIResponse[UserResponse])
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = auth_service.register_user(user_in, db)
    return APIResponse(status_code=200, message="Registration successful", data=user)

@router.post("/login", response_model=APIResponse[Token])
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    token = auth_service.login_user(user_in, db)
    return APIResponse(status_code=200, message="Login successful", data=token)

@router.post("/refresh-token", response_model=APIResponse[Token])
def refresh_access_token(token_in: TokenRefresh, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token_in.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("email")
        token_type: str = payload.get("type")
        if email is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    access_token = create_access_token(data={"email": user.email, "sub": str(user.id)})
    refresh_token = create_refresh_token(data={"email": user.email, "sub": str(user.id)})
    
    return APIResponse(status_code=200, message="Token refreshed", data=Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer"))

@router.post("/forgot-password", response_model=APIResponse[dict])
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    result = auth_service.forgot_password(body.email, db)
    return APIResponse(status_code=200, message=result["message"], data={})

@router.post("/verify-otp", response_model=APIResponse[dict])
def verify_otp(body: VerifyOTPRequest, db: Session = Depends(get_db)):
    auth_service.verify_otp(body.email, body.otp, db)
    return APIResponse(status_code=200, message="OTP verified successfully.", data={"valid": True})

@router.post("/reset-password", response_model=APIResponse[dict])
def reset_password(body: ResetPasswordWithOTPRequest, db: Session = Depends(get_db)):
    auth_service.reset_password_with_otp(body.email, body.otp, body.new_password, db)
    return APIResponse(status_code=200, message="Password reset successfully.", data={})
