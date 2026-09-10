from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.subject import SubjectCreateRequest, SubjectUpdateRequest
from app.services import subject_service
from app.utils.response import success


router = APIRouter(prefix="/subjects", tags=["科目与标签模块"])


@router.get("")
def subjects(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return success(subject_service.list_subjects(db))


@router.post("")
def create(payload: SubjectCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return success(subject_service.create_subject(db, payload))


@router.put("/{subject_id}")
def update(subject_id: int, payload: SubjectUpdateRequest, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return success(subject_service.update_subject(db, subject_id, payload))


@router.delete("/{subject_id}")
def delete(subject_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return success(subject_service.delete_subject(db, subject_id))
