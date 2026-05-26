from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AppException
from app.models.user import User
from app.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise AppException("登录已过期或 token 无效", code=401, http_status=401)
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise AppException("用户不存在", code=401, http_status=401)
    if user.status == "disabled":
        raise AppException("账号已被禁用", code=403, http_status=403)
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise AppException("权限不足，需要管理员权限", code=403, http_status=403)
    return current_user
