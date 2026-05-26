from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.wrong_record import WrongRecordUpdateRequest, WrongReviewAttemptCreateRequest
from app.services import wrong_record_service
from app.utils.response import page_data, success


router = APIRouter(prefix="/wrong-records", tags=["错题整理模块"])


@router.get("")
def records(
    keyword: str | None = None,
    subject: str | None = None,
    knowledgePoint: str | None = None,
    masteryStatus: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows, total, page, page_size = wrong_record_service.list_records(
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


@router.get("/statistics")
def statistics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(wrong_record_service.statistics(db, current_user))


@router.get("/knowledge-stats")
def knowledge_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(wrong_record_service.knowledge_stats(db, current_user))


@router.put("/{record_id}")
def update(record_id: int, payload: WrongRecordUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(wrong_record_service.update_record(db, record_id, current_user, payload))


@router.post("/{record_id}/attempts")
def create_attempt(
    record_id: int,
    payload: WrongReviewAttemptCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success(wrong_record_service.create_attempt(db, record_id, current_user, payload))


@router.get("/{record_id}/attempts")
def attempts(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(wrong_record_service.list_attempts(db, record_id, current_user))


@router.post("/{record_id}/master")
def master(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(wrong_record_service.master_record(db, record_id, current_user))


@router.post("/{record_id}/reopen")
def reopen(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(wrong_record_service.reopen_record(db, record_id, current_user))
