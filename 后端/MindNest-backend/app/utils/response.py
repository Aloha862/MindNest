from typing import Any

from fastapi.responses import JSONResponse

from app.utils.time_utils import format_datetime, now


def success(data: Any = None, message: str = "success", code: int = 200) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data if data is not None else {},
        "timestamp": format_datetime(now()),
    }


def fail(message: str, code: int = 400, data: Any = None) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": format_datetime(now()),
    }


def page_data(items: list[Any], total: int, page: int, page_size: int) -> dict[str, Any]:
    return {"list": items, "total": total, "page": page, "pageSize": page_size}


def error_response(message: str, code: int = 400, http_status: int | None = None) -> JSONResponse:
    return JSONResponse(status_code=http_status or code, content=fail(message=message, code=code))
