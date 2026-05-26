from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile as FastAPIUploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.upload_file import UploadFile
from app.models.user import User
from app.services.serializers import file_out
from app.services.system_config_service import upload_policy
from app.utils.file_utils import (
    build_safe_filename,
    ensure_upload_dirs,
    normalize_file_type,
    path_to_upload_url,
    validate_image_file,
)
from app.utils.pagination import paginate


async def save_upload(
    db: Session,
    *,
    current_user: User,
    file: FastAPIUploadFile,
    file_type: str,
    subject_hint: str = "",
    remark: str = "",
    batch_id: str = "",
    batch_order: int = 0,
) -> dict:
    ensure_upload_dirs()
    content = await file.read()
    try:
        allowed_extensions, max_size = upload_policy(db)
        ext = validate_image_file(file, len(content), allowed_extensions, max_size)
    except ValueError as exc:
        raise AppException(str(exc)) from exc
    safe_name = build_safe_filename(file.filename or "image", ext)
    target_path = Path("app/uploads/original") / safe_name
    absolute_path = Path(__file__).resolve().parent.parent.parent / target_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(content)
    file_url = path_to_upload_url(absolute_path)
    db_file = UploadFile(
        user_id=current_user.id,
        file_name=file.filename or safe_name,
        file_type=normalize_file_type(file_type),
        batch_id=batch_id,
        batch_order=batch_order,
        file_url=file_url,
        original_path=str(absolute_path),
        size=len(content),
        status="uploaded",
        remark=remark or subject_hint or "",
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return file_out(db_file)


async def save_batch_upload(
    db: Session,
    *,
    current_user: User,
    files: list[FastAPIUploadFile],
    file_type: str,
    subject_hint: str = "",
    remark: str = "",
) -> dict:
    batch_id = uuid4().hex
    success_items: list[dict] = []
    failed_items: list[dict] = []
    for index, item in enumerate(files, start=1):
        try:
            success_items.append(
                await save_upload(
                    db,
                    current_user=current_user,
                    file=item,
                    file_type=file_type,
                    subject_hint=subject_hint,
                    remark=remark,
                    batch_id=batch_id,
                    batch_order=index,
                )
            )
        except Exception as exc:
            failed_items.append({"fileName": item.filename, "message": str(exc)})
    return {
        "batchId": batch_id,
        "success": success_items,
        "failed": failed_items,
        "total": len(files),
        "successCount": len(success_items),
        "failedCount": len(failed_items),
    }


def list_files(
    db: Session,
    *,
    current_user: User | None = None,
    keyword: str | None = None,
    file_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    all_users: bool = False,
) -> tuple[list[dict], int, int, int]:
    statement = select(UploadFile)
    if current_user and not all_users and current_user.role != "admin":
        statement = statement.where(UploadFile.user_id == current_user.id)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.where(or_(UploadFile.file_name.like(like), UploadFile.remark.like(like)))
    if file_type:
        statement = statement.where(UploadFile.file_type == normalize_file_type(file_type))
    if status:
        statement = statement.where(UploadFile.status == status)
    statement = statement.order_by(UploadFile.created_at.desc())
    rows, total, page, page_size = paginate(db, statement, page, page_size)
    return [file_out(row) for row in rows], total, page, page_size


def get_file_or_404(db: Session, file_id: int, current_user: User | None = None) -> UploadFile:
    file = db.get(UploadFile, file_id)
    if not file:
        raise AppException("文件不存在", code=404, http_status=404)
    if current_user and current_user.role != "admin" and file.user_id != current_user.id:
        raise AppException("无权访问该文件", code=403, http_status=403)
    return file


def get_file_detail(db: Session, file_id: int, current_user: User) -> dict:
    return file_out(get_file_or_404(db, file_id, current_user))


def delete_file(db: Session, file_id: int, current_user: User) -> dict:
    file = get_file_or_404(db, file_id, current_user)
    for path in [file.original_path, file.processed_path]:
        if path and Path(path).exists():
            try:
                Path(path).unlink()
            except OSError:
                pass
    db.delete(file)
    db.commit()
    return {"id": file_id}
