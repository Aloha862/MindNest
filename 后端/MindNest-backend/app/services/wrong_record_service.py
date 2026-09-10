from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.question import Question
from app.models.user import User
from app.models.wrong_record import WrongRecord
from app.models.wrong_review_attempt import WrongReviewAttempt
from app.schemas.wrong_record import WrongRecordCreateRequest, WrongRecordUpdateRequest, WrongReviewAttemptCreateRequest
from app.services.serializers import attempt_out, parse_json_list, wrong_record_out
from app.utils.pagination import paginate
from app.utils.time_utils import now


def _scope(statement, current_user: User, all_users: bool = False):
    if current_user.role != "admin" or not all_users:
        return statement.where(WrongRecord.user_id == current_user.id)
    return statement


def get_record_or_404(db: Session, record_id: int, current_user: User) -> WrongRecord:
    record = db.get(WrongRecord, record_id)
    if not record:
        raise AppException("错题记录不存在", code=404, http_status=404)
    if current_user.role != "admin" and record.user_id != current_user.id:
        raise AppException("无权访问该错题记录", code=403, http_status=403)
    return record


def mark_wrong(db: Session, question_id: int, current_user: User, payload: WrongRecordCreateRequest) -> dict:
    question = db.get(Question, question_id)
    if not question:
        raise AppException("题目不存在", code=404, http_status=404)
    if current_user.role != "admin" and question.user_id != current_user.id:
        raise AppException("无权操作该题目", code=403, http_status=403)
    exists = db.scalar(select(WrongRecord).where(WrongRecord.question_id == question_id, WrongRecord.user_id == current_user.id))
    if exists:
        exists.note = payload.note or exists.note
        exists.mastery_status = payload.masteryStatus or exists.mastery_status
        exists.source = payload.source or exists.source
        db.commit()
        db.refresh(exists)
        return wrong_record_out(exists, include_question=True)
    record = WrongRecord(
        question_id=question.id,
        user_id=current_user.id,
        file_id=question.file_id,
        task_id=question.task_id,
        note=payload.note,
        mastery_status=payload.masteryStatus,
        source=payload.source,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return wrong_record_out(record, include_question=True)


def unmark_wrong(db: Session, question_id: int, current_user: User) -> dict:
    record = db.scalar(select(WrongRecord).where(WrongRecord.question_id == question_id, WrongRecord.user_id == current_user.id))
    if not record:
        raise AppException("错题记录不存在", code=404, http_status=404)
    db.delete(record)
    db.commit()
    return {"questionId": question_id}


def list_records(
    db: Session,
    *,
    current_user: User,
    keyword: str | None = None,
    subject: str | None = None,
    knowledge_point: str | None = None,
    mastery_status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    all_users: bool = False,
) -> tuple[list[dict], int, int, int]:
    statement = _scope(select(WrongRecord), current_user, all_users).join(Question, Question.id == WrongRecord.question_id)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.where(or_(Question.title.like(like), Question.content.like(like), WrongRecord.note.like(like)))
    if subject:
        statement = statement.where(Question.subject == subject)
    if knowledge_point:
        statement = statement.where(Question.knowledge_points.like(f"%{knowledge_point}%"))
    if mastery_status:
        statement = statement.where(WrongRecord.mastery_status == mastery_status)
    statement = statement.order_by(WrongRecord.updated_at.desc())
    rows, total, page, page_size = paginate(db, statement, page, page_size)
    return [wrong_record_out(row, include_question=True) for row in rows], total, page, page_size


def update_record(db: Session, record_id: int, current_user: User, payload: WrongRecordUpdateRequest) -> dict:
    record = get_record_or_404(db, record_id, current_user)
    if payload.note is not None:
        record.note = payload.note
    if payload.masteryStatus is not None:
        record.mastery_status = payload.masteryStatus
    if payload.reviewCount is not None:
        record.review_count = max(0, payload.reviewCount)
        record.last_review_time = now()
    if payload.increaseReviewCount:
        record.review_count += 1
        record.last_review_time = now()
    db.commit()
    db.refresh(record)
    return wrong_record_out(record, include_question=True)


def create_attempt(db: Session, record_id: int, current_user: User, payload: WrongReviewAttemptCreateRequest) -> dict:
    record = get_record_or_404(db, record_id, current_user)
    result = (payload.result or "").strip().lower()
    rating = (payload.selfRating or "normal").strip().lower()
    if result not in {"correct", "wrong", "unsure"}:
        raise AppException("复习结果只能是 correct、wrong 或 unsure")
    if rating not in {"easy", "normal", "hard"}:
        raise AppException("自评难度只能是 easy、normal 或 hard")
    attempt = WrongReviewAttempt(
        wrong_record_id=record.id,
        user_id=current_user.id,
        question_id=record.question_id,
        result=result,
        self_rating=rating,
        note=payload.note or "",
    )
    record.review_count += 1
    record.last_review_time = now()
    if result == "correct":
        record.mastery_status = "reviewing"
        recent = sorted(record.attempts or [], key=lambda item: item.created_at or "", reverse=True)[:1]
        if recent and all(item.result == "correct" for item in recent):
            record.mastery_status = "mastered"
    else:
        record.mastery_status = "weak"
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    db.refresh(record)
    return {"attempt": attempt_out(attempt), "record": wrong_record_out(record, include_question=True)}


def list_attempts(db: Session, record_id: int, current_user: User) -> list[dict]:
    record = get_record_or_404(db, record_id, current_user)
    attempts = db.scalars(
        select(WrongReviewAttempt)
        .where(WrongReviewAttempt.wrong_record_id == record.id)
        .order_by(WrongReviewAttempt.created_at.desc())
    ).all()
    return [attempt_out(item) for item in attempts]


def master_record(db: Session, record_id: int, current_user: User) -> dict:
    record = get_record_or_404(db, record_id, current_user)
    record.mastery_status = "mastered"
    record.last_review_time = now()
    db.commit()
    db.refresh(record)
    return wrong_record_out(record, include_question=True)


def reopen_record(db: Session, record_id: int, current_user: User) -> dict:
    record = get_record_or_404(db, record_id, current_user)
    record.mastery_status = "reviewing"
    db.commit()
    db.refresh(record)
    return wrong_record_out(record, include_question=True)


def knowledge_stats(db: Session, current_user: User, all_users: bool = False) -> list[dict]:
    statement = _scope(select(WrongRecord), current_user, all_users).join(Question, Question.id == WrongRecord.question_id)
    rows = db.scalars(statement).all()
    result: dict[str, dict] = {}
    for record in rows:
        points = parse_json_list(record.question.knowledge_points_json) or parse_json_list(record.question.knowledge_points)
        for point in points:
            item = result.setdefault(
                point,
                {"name": point, "value": 0, "wrongCount": 0, "masteredCount": 0, "weakCount": 0, "reviewingCount": 0},
            )
            item["value"] += 1
            item["wrongCount"] += 1
            if record.mastery_status == "mastered":
                item["masteredCount"] += 1
            elif record.mastery_status == "weak":
                item["weakCount"] += 1
            elif record.mastery_status == "reviewing":
                item["reviewingCount"] += 1
    return sorted(result.values(), key=lambda item: (item["wrongCount"], item["value"]), reverse=True)


def statistics(db: Session, current_user: User, all_users: bool = False) -> dict:
    total_stmt = select(func.count(WrongRecord.id))
    mastery_stmt = select(WrongRecord.mastery_status, func.count(WrongRecord.id)).group_by(WrongRecord.mastery_status)
    subject_stmt = select(Question.subject, func.count(WrongRecord.id)).join(Question, Question.id == WrongRecord.question_id).group_by(Question.subject)
    type_stmt = select(Question.question_type, func.count(WrongRecord.id)).join(Question, Question.id == WrongRecord.question_id).group_by(Question.question_type)
    if current_user.role != "admin" or not all_users:
        total_stmt = total_stmt.where(WrongRecord.user_id == current_user.id)
        mastery_stmt = mastery_stmt.where(WrongRecord.user_id == current_user.id)
        subject_stmt = subject_stmt.where(WrongRecord.user_id == current_user.id)
        type_stmt = type_stmt.where(WrongRecord.user_id == current_user.id)
    return {
        "total": db.scalar(total_stmt) or 0,
        "masteryDistribution": [{"name": name or "unreviewed", "value": count} for name, count in db.execute(mastery_stmt).all()],
        "subjectDistribution": [{"name": name or "未知", "value": count} for name, count in db.execute(subject_stmt).all()],
        "questionTypeDistribution": [{"name": name or "未知", "value": count} for name, count in db.execute(type_stmt).all()],
    }
