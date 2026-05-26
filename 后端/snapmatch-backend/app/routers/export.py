from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.export import ExportRequest
from app.services import export_service


router = APIRouter(prefix="/export", tags=["导出中心"])


@router.post("")
def export_questions(payload: ExportRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    content, media_type, filename = export_service.build_export(db, current_user, payload)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
