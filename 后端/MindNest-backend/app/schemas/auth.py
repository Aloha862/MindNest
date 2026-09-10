from pydantic import Field, field_validator

from app.schemas.common import CamelModel


class RegisterRequest(CamelModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    confirmPassword: str = Field(min_length=6, max_length=128)
    nickname: str = ""
    phone: str = ""

    @field_validator("confirmPassword")
    @classmethod
    def password_match(cls, value: str, info):
        if info.data.get("password") and value != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return value


class LoginRequest(CamelModel):
    username: str
    password: str


class PasswordChangeRequest(CamelModel):
    oldPassword: str
    newPassword: str = Field(min_length=6, max_length=128)
    confirmPassword: str = Field(min_length=6, max_length=128)

    @field_validator("confirmPassword")
    @classmethod
    def password_match(cls, value: str, info):
        if info.data.get("newPassword") and value != info.data["newPassword"]:
            raise ValueError("两次输入的新密码不一致")
        return value
