from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.user import User
from app.schemas.auth import LoginRequest, PasswordChangeRequest, RegisterRequest
from app.security import create_access_token, hash_password, verify_password
from app.services.serializers import user_detail, user_info
from app.utils.time_utils import now


def register(db: Session, payload: RegisterRequest) -> dict:
    exists = db.scalar(select(User).where(User.username == payload.username))
    if exists:
        raise AppException("用户名已存在")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname or payload.username,
        phone=payload.phone or "",
        role="user",
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "message": "注册成功"}


def login(db: Session, payload: LoginRequest) -> dict:
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppException("用户名或密码错误")
    if user.status == "disabled":
        raise AppException("账号已被禁用", code=403, http_status=403)
    user.last_login_time = now()
    db.commit()
    token = create_access_token(user.id, {"role": user.role})
    return {"token": token, "userInfo": user_info(user)}


def me(user: User) -> dict:
    return user_detail(user)


def change_password(db: Session, user: User, payload: PasswordChangeRequest) -> dict:
    if not verify_password(payload.oldPassword, user.password_hash):
        raise AppException("旧密码错误")
    user.password_hash = hash_password(payload.newPassword)
    db.commit()
    return {"message": "密码修改成功"}
