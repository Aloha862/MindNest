from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.subject import Subject
from app.schemas.subject import SubjectCreateRequest, SubjectUpdateRequest
from app.services.serializers import subject_out


def list_subjects(db: Session) -> list[dict]:
    subjects = db.scalars(select(Subject).order_by(Subject.id.asc())).all()
    return [subject_out(item) for item in subjects]


def create_subject(db: Session, payload: SubjectCreateRequest) -> dict:
    exists = db.scalar(select(Subject).where(Subject.name == payload.name))
    if exists:
        raise AppException("科目名称已存在")
    subject = Subject(name=payload.name, description=payload.description)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject_out(subject)


def update_subject(db: Session, subject_id: int, payload: SubjectUpdateRequest) -> dict:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppException("科目不存在", code=404, http_status=404)
    data = payload.model_dump(exclude_unset=True)
    if data.get("name"):
        exists = db.scalar(select(Subject).where(Subject.name == data["name"], Subject.id != subject_id))
        if exists:
            raise AppException("科目名称已存在")
    for key, value in data.items():
        if value is not None:
            setattr(subject, key, value)
    db.commit()
    db.refresh(subject)
    return subject_out(subject)


def delete_subject(db: Session, subject_id: int) -> dict:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppException("科目不存在", code=404, http_status=404)
    db.delete(subject)
    db.commit()
    return {"id": subject_id}
