import json
from collections import Counter
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.question import Question
from app.models.user import User
from app.models.wrong_record import WrongRecord
from app.schemas.question import QuestionCreateRequest, QuestionUpdateRequest
from app.services.serializers import parse_json_list, question_out
from app.utils.pagination import paginate


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _apply_scope(statement, current_user: User, all_users: bool = False):
    if current_user.role != "admin" or not all_users:
        return statement.where(Question.user_id == current_user.id)
    return statement


def _wrong_record_for_question(db: Session, question: Question, current_user: User | None = None) -> WrongRecord | None:
    statement = select(WrongRecord).where(WrongRecord.question_id == question.id)
    if current_user and current_user.role != "admin":
        statement = statement.where(WrongRecord.user_id == current_user.id)
    return db.scalars(statement.order_by(WrongRecord.created_at.desc())).first()


def list_questions(
    db: Session,
    *,
    current_user: User,
    keyword: str | None = None,
    subject: str | None = None,
    question_type: str | None = None,
    difficulty: str | None = None,
    knowledge_point: str | None = None,
    only_wrong: bool = False,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
    all_users: bool = False,
) -> tuple[list[dict], int, int, int]:
    statement = _apply_scope(select(Question), current_user, all_users)
    if only_wrong:
        statement = statement.join(WrongRecord, WrongRecord.question_id == Question.id)
        if current_user.role != "admin" or not all_users:
            statement = statement.where(WrongRecord.user_id == current_user.id)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.where(or_(Question.title.like(like), Question.content.like(like), Question.analysis_summary.like(like)))
    if subject:
        statement = statement.where(Question.subject == subject)
    if question_type:
        statement = statement.where(Question.question_type == question_type)
    if difficulty:
        statement = statement.where(Question.difficulty == difficulty)
    if knowledge_point:
        statement = statement.where(Question.knowledge_points.like(f"%{knowledge_point}%"))
    start = _parse_time(start_time)
    end = _parse_time(end_time)
    if start:
        statement = statement.where(Question.created_at >= start)
    if end:
        statement = statement.where(Question.created_at <= end)
    statement = statement.order_by(Question.created_at.desc()).distinct()
    rows, total, page, page_size = paginate(db, statement, page, page_size)
    return [question_out(row, _wrong_record_for_question(db, row, current_user)) for row in rows], total, page, page_size


def get_question_or_404(db: Session, question_id: int, current_user: User) -> Question:
    question = db.get(Question, question_id)
    if not question:
        raise AppException("题目不存在", code=404, http_status=404)
    if current_user.role != "admin" and question.user_id != current_user.id:
        raise AppException("无权访问该题目", code=403, http_status=403)
    return question


def get_question(db: Session, question_id: int, current_user: User) -> dict:
    question = get_question_or_404(db, question_id, current_user)
    return question_out(question, _wrong_record_for_question(db, question, current_user))


def create_question(db: Session, payload: QuestionCreateRequest, current_user: User) -> dict:
    raw_vlm = {
        "detailedAnalysis": payload.detailedAnalysis,
        "solutionSteps": payload.solutionSteps,
        "commonMistakes": payload.commonMistakes,
        "errorCauseTags": payload.errorCauseTags,
        "reviewPlan": payload.reviewPlan,
        "similarPracticeSuggestions": payload.similarPracticeSuggestions,
        "estimatedTime": payload.estimatedTime,
        "formulas": payload.formulas,
        "answer": payload.answer,
        "analysisSummary": payload.analysisSummary,
    }
    question = Question(
        task_id=payload.taskId,
        file_id=payload.fileId,
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        subject=payload.subject,
        question_type=payload.questionType,
        knowledge_points=json.dumps(payload.knowledgePoints, ensure_ascii=False),
        options_json=payload.options or [],
        knowledge_points_json=payload.knowledgePoints or [],
        formulas_json=payload.formulas or [],
        raw_vlm_json=raw_vlm,
        confidence=payload.confidence or 0,
        review_status=payload.reviewStatus,
        difficulty=payload.difficulty,
        answer=payload.answer,
        analysis_summary=payload.analysisSummary,
        source_image_url=payload.sourceImageUrl,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question_out(question)


def update_question(db: Session, question_id: int, payload: QuestionUpdateRequest, current_user: User) -> dict:
    question = get_question_or_404(db, question_id, current_user)
    data = payload.model_dump(exclude_unset=True)
    mapping = {
        "questionType": "question_type",
        "knowledgePoints": "knowledge_points",
        "analysisSummary": "analysis_summary",
        "sourceImageUrl": "source_image_url",
        "options": "options_json",
        "formulas": "formulas_json",
        "reviewStatus": "review_status",
    }
    raw_keys = {
        "detailedAnalysis",
        "solutionSteps",
        "commonMistakes",
        "errorCauseTags",
        "reviewPlan",
        "similarPracticeSuggestions",
        "estimatedTime",
        "formulas",
        "answer",
        "analysisSummary",
    }
    raw_vlm = question.raw_vlm_json or {}
    for key, value in data.items():
        attr = mapping.get(key, key)
        if key == "knowledgePoints":
            value = json.dumps(value or [], ensure_ascii=False)
            question.knowledge_points_json = data.get("knowledgePoints") or []
        if key in raw_keys:
            raw_vlm[key] = value
        if hasattr(question, attr):
            setattr(question, attr, value)
    question.raw_vlm_json = raw_vlm
    db.commit()
    db.refresh(question)
    return question_out(question, _wrong_record_for_question(db, question, current_user))


def delete_question(db: Session, question_id: int, current_user: User) -> dict:
    question = get_question_or_404(db, question_id, current_user)
    db.delete(question)
    db.commit()
    return {"id": question_id}


def distribution(db: Session, column, current_user: User | None = None, all_users: bool = False) -> list[dict]:
    statement = select(column, func.count(Question.id)).group_by(column)
    if current_user and current_user.role != "admin" and not all_users:
        statement = statement.where(Question.user_id == current_user.id)
    return [{"name": name or "未知", "value": count} for name, count in db.execute(statement).all()]


def tag_distribution(db: Session, current_user: User | None = None, all_users: bool = False) -> list[dict]:
    statement = select(Question.knowledge_points)
    if current_user and current_user.role != "admin" and not all_users:
        statement = statement.where(Question.user_id == current_user.id)
    counter: Counter[str] = Counter()
    for value in db.scalars(statement).all():
        counter.update(item for item in parse_json_list(value) if item)
    return [{"name": name, "value": value} for name, value in counter.most_common()]


def knowledge_stats(db: Session, current_user: User, all_users: bool = False) -> list[dict]:
    statement = select(Question)
    if current_user.role != "admin" or not all_users:
        statement = statement.where(Question.user_id == current_user.id)
    rows = db.scalars(statement).all()
    result: dict[str, dict] = {}
    for question in rows:
        points = parse_json_list(question.knowledge_points_json) or parse_json_list(question.knowledge_points)
        wrong_records = question.wrong_records or []
        is_wrong = bool(wrong_records)
        is_mastered = any(record.mastery_status == "mastered" for record in wrong_records)
        is_weak = any(record.mastery_status == "weak" for record in wrong_records)
        for point in points:
            item = result.setdefault(
                point,
                {
                    "name": point,
                    "value": 0,
                    "wrongCount": 0,
                    "masteredCount": 0,
                    "weakCount": 0,
                    "subjectCounts": {},
                },
            )
            item["value"] += 1
            subject = question.subject or "其他"
            item["subjectCounts"][subject] = item["subjectCounts"].get(subject, 0) + 1
            if is_wrong:
                item["wrongCount"] += 1
            if is_mastered:
                item["masteredCount"] += 1
            if is_weak:
                item["weakCount"] += 1
    rows = []
    for item in result.values():
        subject_counts = item.get("subjectCounts") or {}
        item["subjects"] = sorted(subject_counts, key=subject_counts.get, reverse=True)
        item["subject"] = item["subjects"][0] if item["subjects"] else ""
        rows.append(item)
    return sorted(rows, key=lambda item: item["value"], reverse=True)


def tags(db: Session, current_user: User) -> list[dict]:
    return tag_distribution(db, current_user)


def statistics(db: Session, current_user: User) -> dict:
    base = select(func.count(Question.id))
    wrong_base = select(func.count(WrongRecord.id))
    if current_user.role != "admin":
        base = base.where(Question.user_id == current_user.id)
        wrong_base = wrong_base.where(WrongRecord.user_id == current_user.id)
    return {
        "total": db.scalar(base) or 0,
        "wrongCount": db.scalar(wrong_base) or 0,
        "subjectDistribution": distribution(db, Question.subject, current_user),
        "questionTypeDistribution": distribution(db, Question.question_type, current_user),
        "difficultyDistribution": distribution(db, Question.difficulty, current_user),
        "knowledgePointDistribution": tag_distribution(db, current_user),
    }
