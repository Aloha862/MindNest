from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import AppException
from app.models.user import User
from app.schemas.focus import FocusEndRequest, FocusFrameAnalyzeRequest, FocusStartRequest, FocusStateRequest
from app.services import focus_service
from app.utils.response import success


router = APIRouter(prefix="/focus", tags=["专注监督模块"])


@router.post("/start")
def start(payload: FocusStartRequest = FocusStartRequest(), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(focus_service.start_session(db, current_user, payload))


@router.get("/current")
def current(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(focus_service.current_session(db, current_user))


@router.post("/state")
def state(payload: FocusStateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(focus_service.submit_state(db, current_user, payload))


@router.post("/analyze-frame")
async def analyze_frame(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    content_type = request.headers.get("content-type", "")
    image_bytes = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        frame = form.get("frame")
        if not isinstance(frame, UploadFile):
            raise AppException("缺少压缩抽帧文件", 400)
        image_bytes = await frame.read()
        payload = FocusFrameAnalyzeRequest(
            sessionId=int(form.get("sessionId") or 0),
            imageData="",
            clientState=str(form.get("clientState") or "unknown"),
            clientConfidence=float(form.get("clientConfidence") or 0),
            clientPosture=str(form.get("clientPosture") or ""),
            clientFocusScore=int(float(form.get("clientFocusScore") or 0)),
            capturedAt=str(form.get("capturedAt") or ""),
        )
    else:
        payload = FocusFrameAnalyzeRequest.model_validate(await request.json())

    return success(focus_service.analyze_frame(db, current_user, payload, image_bytes=image_bytes))


@router.post("/end")
def end(payload: FocusEndRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(focus_service.end_session(db, current_user, payload.sessionId))
