from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.system_config import SystemConfigPayload
from app.schemas.user import UserStatusUpdateRequest
from app.services import admin_service, system_config_service
from app.utils.response import page_data, success


router = APIRouter(prefix="/admin", tags=["管理员模块"], dependencies=[Depends(require_admin)])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return success(admin_service.dashboard(db))


@router.get("/users")
def users(
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
):
    rows, total, page, page_size = admin_service.list_users(db, keyword=keyword, role=role, status=status, page=page, page_size=pageSize)
    return success(page_data(rows, total, page, page_size))


@router.put("/users/{user_id}/status")
def update_status(user_id: int, payload: UserStatusUpdateRequest, db: Session = Depends(get_db)):
    return success(admin_service.update_user_status(db, user_id, payload))


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return success(admin_service.delete_user(db, user_id))


@router.get("/files")
def files(
    keyword: str | None = None,
    fileType: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rows, total, page, page_size = admin_service.admin_list_files(
        db,
        current_user=current_user,
        keyword=keyword,
        file_type=fileType,
        status=status,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.delete("/files/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return success(admin_service.admin_delete_file(db, file_id, current_user))


@router.get("/recognition-tasks")
def recognition_tasks(
    keyword: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    startTime: str | None = None,
    endTime: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rows, total, page, page_size = admin_service.admin_list_tasks(
        db,
        current_user=current_user,
        keyword=keyword,
        status=status,
        page=page,
        page_size=pageSize,
        start_time=startTime,
        end_time=endTime,
    )
    return success(page_data(rows, total, page, page_size))


@router.get("/questions")
def questions(
    keyword: str | None = None,
    subject: str | None = None,
    questionType: str | None = None,
    difficulty: str | None = None,
    knowledgePoint: str | None = None,
    onlyWrong: bool = False,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rows, total, page, page_size = admin_service.admin_list_questions(
        db,
        current_user=current_user,
        keyword=keyword,
        subject=subject,
        question_type=questionType,
        difficulty=difficulty,
        knowledge_point=knowledgePoint,
        only_wrong=onlyWrong,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.get("/model-logs")
def model_logs(
    keyword: str | None = None,
    modelType: str | None = None,
    stage: str | None = None,
    errorCode: str | None = None,
    status: str | None = None,
    startTime: str | None = None,
    endTime: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
):
    rows, total, page, page_size = admin_service.list_model_logs(
        db,
        keyword=keyword,
        model_type=modelType,
        stage=stage,
        error_code=errorCode,
        status=status,
        start_time=startTime,
        end_time=endTime,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.get("/wrong-records")
def wrong_records(
    keyword: str | None = None,
    subject: str | None = None,
    knowledgePoint: str | None = None,
    masteryStatus: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rows, total, page, page_size = admin_service.admin_list_wrong_records(
        db,
        current_user=current_user,
        keyword=keyword,
        subject=subject,
        knowledge_point=knowledgePoint,
        mastery_status=masteryStatus,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.get("/materials")
def materials(
    keyword: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rows, total, page, page_size = admin_service.admin_list_materials(
        db,
        current_user=current_user,
        keyword=keyword,
        category=category,
        tag=tag,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.delete("/materials/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return success(admin_service.admin_delete_material(db, material_id, current_user))


@router.get("/statistics")
def statistics(db: Session = Depends(get_db)):
    return success(admin_service.statistics(db))


@router.get("/review-tasks")
def review_tasks(db: Session = Depends(get_db)):
    return success(admin_service.review_tasks(db))


@router.get("/system-config")
def system_config(db: Session = Depends(get_db)):
    return success(system_config_service.get_config(db))


@router.put("/system-config")
def update_system_config(payload: SystemConfigPayload, db: Session = Depends(get_db)):
    return success(system_config_service.update_config(db, payload))
