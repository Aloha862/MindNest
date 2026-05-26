from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.recognition_task import RecognitionTask
from app.models.subject import Subject
from app.models.upload_file import UploadFile
from app.models.user import User
from app.schemas.user import UserUpdateRequest
from app.services.question_service import distribution
from app.services.serializers import question_out, task_out, user_detail


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
    upload_count = db.scalar(select(func.count(UploadFile.id)).where(UploadFile.user_id == user.id)) or 0
    recognition_count = db.scalar(select(func.count(RecognitionTask.id)).where(RecognitionTask.user_id == user.id)) or 0
    question_count = db.scalar(select(func.count(Question.id)).where(Question.user_id == user.id)) or 0
    subject_count = db.scalar(select(func.count(Subject.id))) or 0
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
    }
