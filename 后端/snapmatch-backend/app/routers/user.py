from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserUpdateRequest
from app.services import user_service
from app.utils.response import success


router = APIRouter(prefix="/user", tags=["用户模块"])


@router.get("/profile")
def profile(current_user: User = Depends(get_current_user)):
    return success(user_service.get_profile(current_user))


@router.put("/profile")
def update_profile(payload: UserUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(user_service.update_profile(db, current_user, payload))


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(user_service.dashboard(db, current_user))
