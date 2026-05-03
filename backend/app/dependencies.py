from fastapi import Depends
from app.models.models import User
from app.core.security import get_current_user as _get_current_user
from app.core.security import get_current_admin as _get_current_admin


def get_current_user(current_user: User = Depends(_get_current_user)) -> User:
    return current_user


def get_current_admin_user(current_user: User = Depends(_get_current_admin)) -> User:
    return current_user
