from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.question import QuestionCreateRequest, QuestionUpdateRequest
from app.schemas.wrong_record import WrongRecordCreateRequest
from app.services import question_service, wrong_record_service
from app.utils.response import page_data, success


router = APIRouter(prefix="/questions", tags=["题目卡片模块"])


@router.get("/statistics")
def statistics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(question_service.statistics(db, current_user))


@router.get("/tags")
def tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(question_service.tags(db, current_user))


@router.get("/knowledge-stats")
def knowledge_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(question_service.knowledge_stats(db, current_user))


@router.get("")
def questions(
    keyword: str | None = None,
    subject: str | None = None,
    questionType: str | None = None,
    difficulty: str | None = None,
    knowledgePoint: str | None = None,
    onlyWrong: bool = False,
    startTime: str | None = None,
    endTime: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows, total, page, page_size = question_service.list_questions(
        db,
        current_user=current_user,
        keyword=keyword,
        subject=subject,
        question_type=questionType,
        difficulty=difficulty,
        knowledge_point=knowledgePoint,
        only_wrong=onlyWrong,
        start_time=startTime,
        end_time=endTime,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.post("")
def create(payload: QuestionCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(question_service.create_question(db, payload, current_user))


@router.get("/{question_id}")
def detail(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(question_service.get_question(db, question_id, current_user))


@router.put("/{question_id}")
def update(question_id: int, payload: QuestionUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(question_service.update_question(db, question_id, payload, current_user))


@router.delete("/{question_id}")
def delete(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(question_service.delete_question(db, question_id, current_user))


@router.post("/{question_id}/wrong")
def mark_wrong(
    question_id: int,
    payload: WrongRecordCreateRequest = WrongRecordCreateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success(wrong_record_service.mark_wrong(db, question_id, current_user, payload))


@router.delete("/{question_id}/wrong")
def unmark_wrong(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(wrong_record_service.unmark_wrong(db, question_id, current_user))
