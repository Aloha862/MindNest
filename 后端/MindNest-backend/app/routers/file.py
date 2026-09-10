from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import file_service
from app.services.system_config_service import get_config
from app.utils.response import page_data, success


router = APIRouter(prefix="/files", tags=["文件上传模块"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    fileType: str = Form("homework"),
    subjectHint: str = Form(""),
    remark: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await file_service.save_upload(
        db,
        current_user=current_user,
        file=file,
        file_type=fileType,
        subject_hint=subjectHint,
        remark=remark,
    )
    return success(data)


@router.post("/batch-upload")
async def batch_upload_file(
    files: list[UploadFile] = File(...),
    fileType: str = Form("homework"),
    subjectHint: str = Form(""),
    remark: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await file_service.save_batch_upload(
        db,
        current_user=current_user,
        files=files,
        file_type=fileType,
        subject_hint=subjectHint,
        remark=remark,
    )
    return success(data)


@router.get("/mine")
def mine(
    keyword: str | None = None,
    fileType: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows, total, page, page_size = file_service.list_files(
        db,
        current_user=current_user,
        keyword=keyword,
        file_type=fileType,
        status=status,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.get("/upload-policy")
def upload_policy(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = get_config(db)
    return success({
        "allowedFileTypes": config["allowedFileTypes"],
        "maxUploadSizeMb": config["maxUploadSizeMb"],
        "ocrEnabled": config["ocrEnabled"],
        "vlmEnabled": config["vlmEnabled"],
    })


@router.get("/{file_id}")
def detail(file_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(file_service.get_file_detail(db, file_id, current_user))


@router.delete("/{file_id}")
def delete(file_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(file_service.delete_file(db, file_id, current_user))
