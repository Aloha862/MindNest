from app.schemas.common import CamelModel


class UserInfo(CamelModel):
    id: int
    username: str
    nickname: str
    avatar: str
    role: str


class UserDetail(CamelModel):
    id: int
    username: str
    nickname: str
    phone: str
    avatar: str
    role: str
    status: str
    createdAt: str
    updatedAt: str
    lastLoginTime: str


class UserUpdateRequest(CamelModel):
    nickname: str | None = None
    phone: str | None = None
    avatar: str | None = None


class UserStatusUpdateRequest(CamelModel):
    status: str
