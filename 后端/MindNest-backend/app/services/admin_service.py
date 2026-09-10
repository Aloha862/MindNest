from datetime import date, datetime, time

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.learning_material import LearningMaterial
from app.models.model_log import ModelLog
from app.models.question import Question
from app.models.recognition_task import RecognitionTask
from app.models.upload_file import UploadFile
from app.models.user import User
from app.models.wrong_record import WrongRecord
from app.schemas.user import UserStatusUpdateRequest
from app.services import material_service, wrong_record_service
from app.services.file_service import delete_file, list_files
from app.services.question_service import distribution, list_questions
from app.services.recognition_service import list_tasks
from app.services.serializers import file_out, log_out, parse_json_dict, question_out, task_out, user_detail
from app.utils.pagination import paginate


def _count(db: Session, model) -> int:
    return db.scalar(select(func.count(model.id))) or 0


def _today_range() -> tuple[datetime, datetime]:
    today = date.today()
    return datetime.combine(today, time.min), datetime.combine(today, time.max)


def _group_count(db: Session, column, model) -> list[dict]:
    return [{"name": name or "未知", "value": count} for name, count in db.execute(select(column, func.count(model.id)).group_by(column)).all()]


def _trend(db: Session, model, column, days: int = 7) -> list[dict]:
    rows = db.execute(
        select(func.date(column), func.count(model.id))
        .group_by(func.date(column))
        .order_by(func.date(column).desc())
        .limit(days)
    ).all()
    return [{"date": str(day), "value": count} for day, count in reversed(rows)]


def dashboard(db: Session) -> dict:
    start, end = _today_range()
    recent_logs = db.scalars(select(ModelLog).order_by(ModelLog.created_at.desc()).limit(8)).all()
    recent_files = db.scalars(select(UploadFile).order_by(UploadFile.created_at.desc()).limit(8)).all()
    base = {
        "userCount": _count(db, User),
        "fileCount": _count(db, UploadFile),
        "recognitionTaskCount": _count(db, RecognitionTask),
        "questionCount": _count(db, Question),
        "wrongRecordCount": _count(db, WrongRecord),
        "materialCount": _count(db, LearningMaterial),
        "todayUploadCount": db.scalar(select(func.count(UploadFile.id)).where(UploadFile.created_at.between(start, end))) or 0,
        "todayRecognitionCount": db.scalar(select(func.count(RecognitionTask.id)).where(RecognitionTask.created_at.between(start, end))) or 0,
        "failedTaskCount": db.scalar(select(func.count(RecognitionTask.id)).where(RecognitionTask.status == "failed")) or 0,
        "modelCallCount": _count(db, ModelLog),
        "taskStatusDistribution": _group_count(db, RecognitionTask.status, RecognitionTask),
        "subjectDistribution": distribution(db, Question.subject, None, all_users=True),
        "fileTypeDistribution": _group_count(db, UploadFile.file_type, UploadFile),
        "uploadTrend": _trend(db, UploadFile, UploadFile.created_at),
        "recognitionTrend": _trend(db, RecognitionTask, RecognitionTask.created_at),
        "recentLogs": [log_out(item) for item in recent_logs],
        "recentFiles": [file_out(item) for item in recent_files],
    }
    base.update(_quality_statistics(db))
    return base


def list_users(
    db: Session,
    *,
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int, int, int]:
    statement = select(User)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.where(or_(User.username.like(like), User.nickname.like(like), User.phone.like(like)))
    if role:
        statement = statement.where(User.role == role)
    if status:
        statement = statement.where(User.status == status)
    statement = statement.order_by(User.created_at.desc())
    rows, total, page, page_size = paginate(db, statement, page, page_size)
    return [user_detail(item) for item in rows], total, page, page_size


def update_user_status(db: Session, user_id: int, payload: UserStatusUpdateRequest) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise AppException("用户不存在", code=404, http_status=404)
    if payload.status not in {"active", "disabled"}:
        raise AppException("用户状态只能是 active 或 disabled")
    user.status = payload.status
    db.commit()
    db.refresh(user)
    return user_detail(user)


def delete_user(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise AppException("用户不存在", code=404, http_status=404)
    db.delete(user)
    db.commit()
    return {"id": user_id}


def list_model_logs(
    db: Session,
    *,
    keyword: str | None = None,
    model_type: str | None = None,
    stage: str | None = None,
    error_code: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int, int, int]:
    statement = select(ModelLog)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.where(or_(ModelLog.model_name.like(like), ModelLog.input_summary.like(like), ModelLog.output_summary.like(like)))
    if model_type:
        statement = statement.where(ModelLog.model_type == model_type)
    if stage:
        statement = statement.where(ModelLog.stage == stage)
    if error_code:
        statement = statement.where(ModelLog.error_code == error_code)
    if status:
        statement = statement.where(ModelLog.status == status)
    if start_time:
        try:
            statement = statement.where(ModelLog.created_at >= datetime.strptime(start_time, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_time:
        try:
            statement = statement.where(ModelLog.created_at <= datetime.strptime(end_time, "%Y-%m-%d"))
        except ValueError:
            pass
    statement = statement.order_by(ModelLog.created_at.desc())
    rows, total, page, page_size = paginate(db, statement, page, page_size)
    return [log_out(item) for item in rows], total, page, page_size


def statistics(db: Session) -> dict:
    data = {
        "userCount": _count(db, User),
        "fileCount": _count(db, UploadFile),
        "recognitionTaskCount": _count(db, RecognitionTask),
        "questionCount": _count(db, Question),
        "wrongRecordCount": _count(db, WrongRecord),
        "materialCount": _count(db, LearningMaterial),
        "taskStatusDistribution": _group_count(db, RecognitionTask.status, RecognitionTask),
        "fileTypeDistribution": _group_count(db, UploadFile.file_type, UploadFile),
        "subjectDistribution": distribution(db, Question.subject, None, all_users=True),
        "questionTypeDistribution": distribution(db, Question.question_type, None, all_users=True),
        "difficultyDistribution": distribution(db, Question.difficulty, None, all_users=True),
        "modelTypeDistribution": _group_count(db, ModelLog.model_type, ModelLog),
        "uploadTrend": _trend(db, UploadFile, UploadFile.created_at),
        "recognitionTrend": _trend(db, RecognitionTask, RecognitionTask.created_at),
        "failedTaskTrend": _trend(db, RecognitionTask, RecognitionTask.created_at),
    }
    data.update(_quality_statistics(db))
    return data


def _percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    index = min(len(values) - 1, max(0, int(round((len(values) - 1) * ratio))))
    return values[index]


def _quality_statistics(db: Session) -> dict:
    logs = db.scalars(select(ModelLog)).all()
    by_type: dict[str, list[int]] = {}
    for log in logs:
        by_type.setdefault(log.model_type or "unknown", []).append(log.cost_time or 0)
    model_latency = [
        {
            "modelType": model_type,
            "avg": round(sum(values) / len(values), 2) if values else 0,
            "p95": _percentile(values, 0.95),
            "count": len(values),
        }
        for model_type, values in sorted(by_type.items())
    ]
    failure_reasons = [
        {"name": name or "UNKNOWN", "value": count}
        for name, count in db.execute(
            select(RecognitionTask.error_code, func.count(RecognitionTask.id))
            .where(RecognitionTask.status == "failed")
            .group_by(RecognitionTask.error_code)
            .order_by(func.count(RecognitionTask.id).desc())
            .limit(10)
        ).all()
    ]
    stage_failures = [
        {"name": name or "unknown", "value": count}
        for name, count in db.execute(
            select(RecognitionTask.error_stage, func.count(RecognitionTask.id))
            .where(RecognitionTask.status == "failed")
            .group_by(RecognitionTask.error_stage)
            .order_by(func.count(RecognitionTask.id).desc())
        ).all()
    ]
    tasks = db.scalars(select(RecognitionTask)).all()
    low_quality_count = sum(1 for task in tasks if parse_json_dict(task.quality_json).get("warnings"))
    review_task_count = sum(1 for task in tasks if task.status == "needs_review")
    review_question_count = db.scalar(select(func.count(Question.id)).where(Question.review_status == "pending")) or 0
    batch_rows = [task for task in tasks if task.batch_id]
    batch_ids = {task.batch_id for task in batch_rows}
    finished_batch_tasks = [task for task in batch_rows if task.status in {"completed", "needs_review", "failed"}]
    batch_success_rate = round(
        (sum(1 for task in batch_rows if task.status in {"completed", "needs_review"}) / len(finished_batch_tasks)) * 100,
        2,
    ) if finished_batch_tasks else 0
    return {
        "modelLatency": model_latency,
        "failureReasons": failure_reasons,
        "stageFailureDistribution": stage_failures,
        "ocrEmptyCount": db.scalar(select(func.count(ModelLog.id)).where(ModelLog.error_code == "OCR_EMPTY")) or 0,
        "vlmInvalidJsonCount": db.scalar(select(func.count(ModelLog.id)).where(ModelLog.error_code == "VLM_INVALID_JSON")) or 0,
        "lowQualityTaskCount": low_quality_count,
        "lowQualityRate": round((low_quality_count / len(tasks)) * 100, 2) if tasks else 0,
        "reviewTaskCount": review_task_count,
        "reviewQuestionCount": review_question_count,
        "reviewRate": round(((review_task_count + review_question_count) / max(1, len(tasks) + _count(db, Question))) * 100, 2),
        "batchCount": len(batch_ids),
        "batchTaskCount": len(batch_rows),
        "batchSuccessRate": batch_success_rate,
    }


def admin_list_files(db: Session, **kwargs):
    return list_files(db, all_users=True, **kwargs)


def admin_delete_file(db: Session, file_id: int, current_user: User):
    return delete_file(db, file_id, current_user)


def admin_list_tasks(db: Session, current_user: User, **kwargs):
    return list_tasks(db, current_user=current_user, all_users=True, **kwargs)


def admin_list_questions(db: Session, current_user: User, **kwargs):
    return list_questions(db, current_user=current_user, all_users=True, **kwargs)


def admin_list_wrong_records(db: Session, current_user: User, **kwargs):
    return wrong_record_service.list_records(db, current_user=current_user, all_users=True, **kwargs)


def admin_list_materials(db: Session, current_user: User, **kwargs):
    return material_service.list_materials(db, current_user=current_user, all_users=True, **kwargs)


def admin_delete_material(db: Session, material_id: int, current_user: User):
    return material_service.delete_material(db, material_id, current_user)


def review_tasks(db: Session) -> dict:
    tasks = db.scalars(
        select(RecognitionTask)
        .where(RecognitionTask.status == "needs_review")
        .order_by(RecognitionTask.updated_at.desc())
        .limit(50)
    ).all()
    questions = db.scalars(
        select(Question)
        .where(or_(Question.review_status == "pending", Question.confidence < 0.65))
        .order_by(Question.updated_at.desc())
        .limit(100)
    ).all()
    return {
        "tasks": [task_out(item) for item in tasks],
        "questions": [question_out(item) for item in questions],
        "taskCount": len(tasks),
        "questionCount": len(questions),
    }
