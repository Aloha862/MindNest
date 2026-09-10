from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import report_service
from app.utils.response import success


router = APIRouter(prefix="/report", tags=["学习报告模块"])


@router.get("/daily")
def daily(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(report_service.daily_report(db, current_user))


@router.get("/sessions")
def sessions(
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return success(report_service.list_sessions(db, current_user, page=page, page_size=pageSize))


@router.get("/sessions/{session_id}")
def session_detail(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(report_service.session_report(db, current_user, session_id))
