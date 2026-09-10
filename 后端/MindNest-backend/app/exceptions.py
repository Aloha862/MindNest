from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.response import fail


class AppException(Exception):
    def __init__(self, message: str, code: int = 400, http_status: int | None = None):
        self.message = message
        self.code = code
        self.http_status = http_status or code


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=fail(exc.message, exc.code))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
        return JSONResponse(status_code=exc.status_code, content=fail(message, exc.status_code))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        message = first.get("msg", "请求参数错误")
        return JSONResponse(status_code=422, content=fail(message, 422))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content=fail(f"服务器内部错误：{exc}", 500))
