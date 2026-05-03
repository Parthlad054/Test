from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import User, RoleEnum
from app.schemas.schemas import UserCreate, UserLogin, Token
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.email import send_otp_email
import random, string
from datetime import datetime, timedelta

def register_user(user_in: UserCreate, db: Session) -> User:
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pass = get_password_hash(user_in.password)
    # Default role is now employee, not admin
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pass,
        full_name=user_in.full_name,
        role=RoleEnum.employee,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def login_user(user_in: UserLogin, db: Session) -> Token:
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"email": user.email, "sub": str(user.id), "role": getattr(user.role, "value", user.role)})
    refresh_token = create_refresh_token(data={"email": user.email, "sub": str(user.id)})
    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

def forgot_password(email: str, db: Session) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Do NOT reveal if email exists — always return success
        return {"message": "If this email is registered, an OTP has been sent."}
    
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    user.otp_used = False
    db.commit()
    
    # Send OTP email
    email_sent = send_otp_email(email, otp)
    if not email_sent:
        # Log the error but don't reveal to user for security
        print(f"Failed to send OTP email to {email}")
    
    return {"message": "OTP sent to your email address."}

def verify_otp(email: str, otp: str, db: Session) -> bool:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or OTP.")
    if user.otp_code != otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP.")
    if user.otp_used:
        raise HTTPException(status_code=400, detail="OTP has already been used.")
    if not user.otp_expires_at or datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    return True

def reset_password_with_otp(email: str, otp: str, new_password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request.")
    
    # Re-verify OTP before resetting
    if user.otp_code != otp or user.otp_used:
        raise HTTPException(status_code=400, detail="Invalid or already used OTP.")
    if not user.otp_expires_at or datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired.")
    
    user.hashed_password = get_password_hash(new_password)
    user.otp_code = None
    user.otp_used = True
    user.otp_expires_at = None
    db.commit()
    return True

def create_admin_user(email: str, password: str, full_name: str, db: Session) -> User:
    """Create an admin user with the specified credentials."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        # If user exists, just update their role to admin
        user.role = RoleEnum.admin
        db.commit()
        db.refresh(user)
        return user
    
    hashed_pass = get_password_hash(password)
    admin_user = User(
        email=email,
        hashed_password=hashed_pass,
        full_name=full_name,
        role=RoleEnum.admin,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user

def promote_to_admin(email: str, db: Session, current_user_email: str = None) -> bool:
    """Promote an employee to admin role. Only admins can perform this action."""
    if current_user_email:
        current_user = db.query(User).filter(User.email == current_user_email).first()
        if not current_user or current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Only admins can promote users.")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user.role == RoleEnum.admin:
        raise HTTPException(status_code=400, detail="User is already an admin.")
    
    user.role = RoleEnum.admin
    db.commit()
    return True

def demote_from_admin(email: str, db: Session, current_user_email: str) -> bool:
    """Demote an admin to employee role. Only admins can perform this action."""
    current_user = db.query(User).filter(User.email == current_user_email).first()
    if not current_user or current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Only admins can demote users.")
    
    # Prevent self-demotion if it's the only admin
    admin_count = db.query(User).filter(User.role == RoleEnum.admin).count()
    if admin_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot demote the last admin.")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user.role != RoleEnum.admin:
        raise HTTPException(status_code=400, detail="User is not an admin.")
    
    user.role = RoleEnum.employee
    db.commit()
    return True
