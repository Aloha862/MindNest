import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def ensure_upload_dirs() -> None:
    (settings.upload_root / "original").mkdir(parents=True, exist_ok=True)
    (settings.upload_root / "processed").mkdir(parents=True, exist_ok=True)


def normalize_file_type(file_type: str) -> str:
    value = (file_type or "homework").strip()
    return "mistake" if value == "wrong" else value


def validate_image_file(
    file: UploadFile,
    size: int,
    allowed_extensions: set[str] | None = None,
    max_size: int | None = None,
) -> str:
    allowed = allowed_extensions or ALLOWED_IMAGE_EXTENSIONS
    limit = max_size or settings.max_upload_size
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        names = "、".join(sorted(item.lstrip(".") for item in allowed))
        raise ValueError(f"只允许上传 {names} 图片")
    if size > limit:
        raise ValueError(f"文件大小不能超过 {max(1, limit // 1024 // 1024)}MB")
    return ext


def build_safe_filename(original_name: str, ext: str) -> str:
    stem = Path(original_name or "image").stem[:40]
    safe_stem = "".join(ch if ch.isalnum() else "_" for ch in stem).strip("_") or "image"
    return f"{safe_stem}_{uuid4().hex}{ext}"


def path_to_upload_url(path: str | os.PathLike[str]) -> str:
    path_obj = Path(path).resolve()
    upload_root = settings.upload_root.resolve()
    relative = path_obj.relative_to(upload_root).as_posix()
    return f"/uploads/{relative}"
