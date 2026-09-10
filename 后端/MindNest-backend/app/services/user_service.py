from datetime import datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.recognition_task import RecognitionTask
from app.models.study_session import StudySession
from app.models.subject import Subject
from app.models.upload_file import UploadFile
from app.models.user import User
from app.models.wrong_record import WrongRecord
from app.schemas.user import UserUpdateRequest
from app.services.question_service import distribution
from app.services.serializers import parse_json_list, question_out, task_out, user_detail


def _today_range() -> tuple[datetime, datetime]:
    current = datetime.now()
    return datetime.combine(current.date(), time.min), datetime.combine(current.date(), time.max)


def get_profile(user: User) -> dict:
    return user_detail(user)


def update_profile(db: Session, user: User, payload: UserUpdateRequest) -> dict:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user_detail(user)


def dashboard(db: Session, user: User) -> dict:
    today_start, today_end = _today_range()
    upload_count = db.scalar(select(func.count(UploadFile.id)).where(UploadFile.user_id == user.id)) or 0
    recognition_count = db.scalar(select(func.count(RecognitionTask.id)).where(RecognitionTask.user_id == user.id)) or 0
    question_count = db.scalar(select(func.count(Question.id)).where(Question.user_id == user.id)) or 0
    subject_count = db.scalar(select(func.count(Subject.id))) or 0
    today_questions = db.scalars(
        select(Question)
        .where(Question.user_id == user.id, Question.created_at >= today_start, Question.created_at <= today_end)
        .order_by(Question.created_at.desc())
    ).all()
    today_wrong_count = db.scalar(
        select(func.count(WrongRecord.id)).where(
            WrongRecord.user_id == user.id,
            WrongRecord.created_at >= today_start,
            WrongRecord.created_at <= today_end,
        )
    ) or 0
    today_sessions = db.scalars(
        select(StudySession).where(StudySession.user_id == user.id, StudySession.start_time >= today_start, StudySession.start_time <= today_end)
    ).all()
    active_session = db.scalars(
        select(StudySession)
        .where(StudySession.user_id == user.id, StudySession.status == "active")
        .order_by(StudySession.start_time.desc())
        .limit(1)
    ).first()
    point_counter: dict[str, int] = {}
    for question in today_questions:
        for point in parse_json_list(question.knowledge_points_json) or parse_json_list(question.knowledge_points):
            point_counter[point] = point_counter.get(point, 0) + 1
    recommended_points = [
        {"name": name, "value": value}
        for name, value in sorted(point_counter.items(), key=lambda item: item[1], reverse=True)[:5]
    ]
    total_focus = sum(item.total_duration for item in today_sessions)
    effective_focus = sum(item.effective_duration for item in today_sessions)
    recent_tasks = db.scalars(
        select(RecognitionTask).where(RecognitionTask.user_id == user.id).order_by(RecognitionTask.created_at.desc()).limit(5)
    ).all()
    recent_questions = db.scalars(
        select(Question).where(Question.user_id == user.id).order_by(Question.created_at.desc()).limit(6)
    ).all()
    return {
        "uploadCount": upload_count,
        "recognitionCount": recognition_count,
        "questionCount": question_count,
        "subjectCount": subject_count,
        "recentTasks": [task_out(item) for item in recent_tasks],
        "recentQuestions": [question_out(item) for item in recent_questions],
        "subjectDistribution": distribution(db, Question.subject, user),
        "questionTypeDistribution": distribution(db, Question.question_type, user),
        "todayFocus": {
            "totalDuration": total_focus,
            "effectiveDuration": effective_focus,
            "focusEfficiency": round(effective_focus / total_focus * 100) if total_focus else 0,
            "sessionCount": len(today_sessions),
            "currentState": "active" if active_session else "idle",
            "currentStateText": "专注进行中" if active_session else "未开始",
        },
        "todayQuestionCount": len(today_questions),
        "todayWrongCount": today_wrong_count,
        "recommendedKnowledgePoints": recommended_points,
    }
