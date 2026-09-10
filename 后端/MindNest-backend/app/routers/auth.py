from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, PasswordChangeRequest, RegisterRequest
from app.services import auth_service
from app.utils.response import success


router = APIRouter(prefix="/auth", tags=["认证模块"])


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return success(auth_service.register(db, payload))


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return success(auth_service.login(db, payload))


@router.post("/logout")
def logout():
    return success(True, message="退出成功")


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return success(auth_service.me(current_user))


@router.put("/password")
def change_password(payload: PasswordChangeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(auth_service.change_password(db, current_user, payload))
