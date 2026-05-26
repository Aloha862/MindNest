from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.recognition import RecognitionBatchStartRequest, RecognitionStartRequest
from app.services import recognition_service
from app.utils.response import page_data, success


router = APIRouter(prefix="/recognition", tags=["识别任务模块"])


@router.post("/start")
def start(
    payload: RecognitionStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = recognition_service.create_recognition_task(db, current_user, payload)
    background_tasks.add_task(recognition_service.run_recognition_task, task["id"], payload.model_dump())
    return success(task, message="识别任务已创建")


@router.post("/batch-start")
def batch_start(
    payload: RecognitionBatchStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = recognition_service.batch_start_recognition(db, current_user, payload)
    for task in result["tasks"]:
        task_payload = RecognitionStartRequest(
            fileId=task["fileId"],
            enablePreprocess=payload.enablePreprocess,
            enableYOLO=payload.enableYOLO,
            enableOCR=payload.enableOCR,
            enableVLM=payload.enableVLM,
        )
        background_tasks.add_task(recognition_service.run_recognition_task, task["id"], task_payload.model_dump())
    return success(result)


@router.get("/tasks")
def tasks(
    keyword: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    startTime: str | None = None,
    endTime: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows, total, page, page_size = recognition_service.list_tasks(
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


@router.get("/tasks/{task_id}")
def task_detail(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(recognition_service.get_task(db, task_id, current_user))


@router.get("/tasks/{task_id}/progress")
def task_progress(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(recognition_service.get_progress(db, task_id, current_user))


@router.get("/tasks/{task_id}/diagnostics")
def task_diagnostics(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(recognition_service.get_diagnostics(db, task_id, current_user))


@router.get("/batches/{batch_id}")
def batch_detail(batch_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(recognition_service.get_batch(db, batch_id, current_user))


@router.post("/tasks/{task_id}/retry")
def retry_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = recognition_service.create_retry_task(db, task_id, current_user)
    background_tasks.add_task(recognition_service.run_recognition_task, result["task"]["id"], RecognitionStartRequest(fileId=result["task"]["fileId"]).model_dump())
    return success(result, message="重试任务已创建")


@router.get("/{task_id}/ocr")
def ocr_result(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(recognition_service.get_ocr_result(db, task_id, current_user))


@router.get("/{task_id}/vlm")
def vlm_result(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(recognition_service.get_vlm_result(db, task_id, current_user))
