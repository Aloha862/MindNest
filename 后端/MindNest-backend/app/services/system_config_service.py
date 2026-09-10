from sqlalchemy.orm import Session

from app.config import settings
from app.models.system_config import SystemConfig
from app.schemas.system_config import SystemConfigPayload


DEFAULT_CONFIG = {
    "ocrEnabled": "true",
    "vlmEnabled": "true",
    "maxUploadSizeMb": str(max(1, settings.max_upload_size // 1024 // 1024)),
    "allowedFileTypes": "jpg, jpeg, png",
    "modelEndpoint": f"{settings.backend_base_url.rstrip('/')}/api",
}


def _bool(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def _int(value: str, fallback: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return fallback


def _rows(db: Session) -> dict[str, str]:
    return {item.key: item.value for item in db.query(SystemConfig).all()}


def get_config(db: Session) -> dict:
    data = {**DEFAULT_CONFIG, **_rows(db)}
    return {
        "ocrEnabled": _bool(data["ocrEnabled"]),
        "vlmEnabled": _bool(data["vlmEnabled"]),
        "backendEnabled": True,
        "maxUploadSizeMb": _int(data["maxUploadSizeMb"], 10),
        "allowedFileTypes": data["allowedFileTypes"],
        "modelEndpoint": data["modelEndpoint"],
    }


def update_config(db: Session, payload: SystemConfigPayload) -> dict:
    values = {
        "ocrEnabled": str(payload.ocrEnabled).lower(),
        "vlmEnabled": str(payload.vlmEnabled).lower(),
        "maxUploadSizeMb": str(max(1, payload.maxUploadSizeMb)),
        "allowedFileTypes": payload.allowedFileTypes or DEFAULT_CONFIG["allowedFileTypes"],
        "modelEndpoint": payload.modelEndpoint or DEFAULT_CONFIG["modelEndpoint"],
    }
    for key, value in values.items():
        row = db.get(SystemConfig, key)
        if row:
            row.value = value
        else:
            db.add(SystemConfig(key=key, value=value))
    db.commit()
    return get_config(db)


def upload_policy(db: Session) -> tuple[set[str], int]:
    config = get_config(db)
    allowed = {
        item.strip().lower().lstrip(".")
        for item in config["allowedFileTypes"].split(",")
        if item.strip()
    }
    if not allowed:
        allowed = {"jpg", "jpeg", "png"}
    max_bytes = config["maxUploadSizeMb"] * 1024 * 1024
    return {f".{item}" for item in allowed}, max_bytes
