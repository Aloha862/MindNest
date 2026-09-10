from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.study_session import StudySession
from app.models.study_state_log import StudyStateLog
from app.models.user import User
from app.schemas.focus import FocusFrameAnalyzeRequest, FocusStartRequest, FocusStateRequest
from app.services.focus_yoloe_service import analyze_focus_frame
from app.utils.time_utils import format_datetime, now


EFFECTIVE_STATES = {"focused", "writing", "computer_learning", "bad_posture"}
PHONE_STATES = {"distracted_phone"}
AWAY_STATES = {"away"}
POSTURE_STATES = {"bad_posture", "fatigue"}

STATE_LABELS = {
    "focused": "专注学习",
    "writing": "低头书写",
    "computer_learning": "看电脑学习",
    "distracted_phone": "手机分心",
    "away": "离开座位",
    "bad_posture": "坐姿提醒",
    "fatigue": "疲劳休息",
    "unknown": "状态未知",
}


def _duration_text(seconds: int) -> str:
    seconds = max(0, int(seconds or 0))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}小时{minutes}分钟"
    if minutes:
        return f"{minutes}分钟{secs}秒"
    return f"{secs}秒"


def _state_label(state: str) -> str:
    return STATE_LABELS.get(state or "unknown", state or "状态未知")


def _is_effective(state: str) -> bool:
    return state in EFFECTIVE_STATES


def _warning_for(payload: FocusStateRequest) -> str:
    if payload.warningType:
        return payload.warningType
    if payload.state == "distracted_phone":
        return "phone"
    if payload.state == "away":
        return "away"
    if payload.state == "bad_posture":
        return "posture"
    if payload.state == "fatigue":
        return "fatigue"
    return ""


def state_log_out(log: StudyStateLog) -> dict:
    return {
        "id": log.id,
        "sessionId": log.session_id,
        "timestamp": format_datetime(log.timestamp),
        "state": log.state,
        "stateLabel": _state_label(log.state),
        "detectedObjects": log.detected_objects_json or [],
        "posture": log.posture,
        "focusScore": log.focus_score,
        "effective": log.effective,
        "warningType": log.warning_type,
        "visionMetadata": log.vision_metadata_json or {},
        "createdAt": format_datetime(log.created_at),
    }


def _ordered_logs(session: StudySession) -> list[StudyStateLog]:
    return sorted(session.state_logs or [], key=lambda item: item.timestamp or item.created_at)


def _segment_counts(logs: list[StudyStateLog], states: set[str]) -> int:
    count = 0
    previous_match = False
    for log in logs:
        current_match = log.state in states
        if current_match and not previous_match:
            count += 1
        previous_match = current_match
    return count


def _calculate_stats(session: StudySession, end_time: datetime | None = None) -> dict:
    end = end_time or session.end_time or now()
    total = max(0, int((end - session.start_time).total_seconds()))
    logs = _ordered_logs(session)
    effective = 0
    phone_duration = 0
    intervals: list[dict] = []

    for index, log in enumerate(logs):
        next_time = logs[index + 1].timestamp if index + 1 < len(logs) else end
        if next_time < log.timestamp:
            continue
        duration = max(0, int((next_time - log.timestamp).total_seconds()))
        if log.state in EFFECTIVE_STATES:
            effective += duration
        if log.state in PHONE_STATES:
            phone_duration += duration
        intervals.append({"state": log.state, "duration": duration})

    scores = [max(0, min(100, int(log.focus_score or 0))) for log in logs]
    avg_score = int(round(sum(scores) / len(scores))) if scores else 0
    return {
        "totalDuration": total,
        "effectiveDuration": effective,
        "distractionCount": _segment_counts(logs, PHONE_STATES),
        "awayCount": _segment_counts(logs, AWAY_STATES),
        "phoneDuration": phone_duration,
        "postureWarningCount": sum(1 for log in logs if log.state in POSTURE_STATES or log.warning_type in {"posture", "fatigue"}),
        "averageFocusScore": avg_score,
        "intervals": intervals,
    }


def _summary(stats: dict) -> str:
    total = stats.get("totalDuration", 0)
    effective = stats.get("effectiveDuration", 0)
    rate = round(effective / total * 100) if total else 0
    return (
        f"本次学习共 {_duration_text(total)}，有效专注 {_duration_text(effective)}，"
        f"专注效率 {rate}%。手机分心 {stats.get('distractionCount', 0)} 次，"
        f"离座 {stats.get('awayCount', 0)} 次。"
    )


def _apply_stats(session: StudySession, stats: dict) -> None:
    session.total_duration = stats["totalDuration"]
    session.effective_duration = stats["effectiveDuration"]
    session.distraction_count = stats["distractionCount"]
    session.away_count = stats["awayCount"]
    session.phone_duration = stats["phoneDuration"]
    session.posture_warning_count = stats["postureWarningCount"]
    session.average_focus_score = stats["averageFocusScore"]
    session.summary = _summary(stats)


def session_out(session: StudySession, *, include_logs: bool = True, live: bool = False) -> dict:
    stats = _calculate_stats(session, now() if live and session.status == "active" else None)
    logs = _ordered_logs(session)
    current_state = logs[-1].state if logs else "unknown"
    return {
        "id": session.id,
        "userId": session.user_id,
        "title": session.title,
        "status": session.status,
        "startTime": format_datetime(session.start_time),
        "endTime": format_datetime(session.end_time),
        "totalDuration": stats["totalDuration"] if live and session.status == "active" else session.total_duration,
        "effectiveDuration": stats["effectiveDuration"] if live and session.status == "active" else session.effective_duration,
        "distractionCount": stats["distractionCount"] if live and session.status == "active" else session.distraction_count,
        "awayCount": stats["awayCount"] if live and session.status == "active" else session.away_count,
        "phoneDuration": stats["phoneDuration"] if live and session.status == "active" else session.phone_duration,
        "postureWarningCount": stats["postureWarningCount"] if live and session.status == "active" else session.posture_warning_count,
        "averageFocusScore": stats["averageFocusScore"] if live and session.status == "active" else session.average_focus_score,
        "summary": _summary(stats) if live and session.status == "active" else session.summary,
        "currentState": current_state,
        "currentStateLabel": _state_label(current_state),
        "logs": [state_log_out(log) for log in logs[-30:]] if include_logs else [],
        "createdAt": format_datetime(session.created_at),
        "updatedAt": format_datetime(session.updated_at),
    }


def get_session_or_404(db: Session, session_id: int, current_user: User) -> StudySession:
    session = db.get(StudySession, session_id)
    if not session or session.user_id != current_user.id:
        raise AppException("学习 session 不存在", 404)
    return session


def start_session(db: Session, current_user: User, payload: FocusStartRequest) -> dict:
    active = db.scalars(
        select(StudySession)
        .where(StudySession.user_id == current_user.id, StudySession.status == "active")
        .order_by(StudySession.start_time.desc())
        .limit(1)
    ).first()
    if active:
        return session_out(active, live=True)

    session = StudySession(user_id=current_user.id, title=payload.title or "学习专注")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session_out(session, live=True)


def current_session(db: Session, current_user: User) -> dict:
    session = db.scalars(
        select(StudySession)
        .where(StudySession.user_id == current_user.id, StudySession.status == "active")
        .order_by(StudySession.start_time.desc())
        .limit(1)
    ).first()
    return session_out(session, live=True) if session else {}


def submit_state(db: Session, current_user: User, payload: FocusStateRequest) -> dict:
    session = get_session_or_404(db, payload.sessionId, current_user)
    if session.status != "active":
        raise AppException("学习 session 已结束，不能继续提交状态", 400)
    state = payload.state or "unknown"
    log = StudyStateLog(
        session_id=session.id,
        user_id=current_user.id,
        state=state,
        detected_objects_json=payload.detectedObjects or [],
        posture=payload.posture or "",
        focus_score=max(0, min(100, int(payload.focusScore or 0))),
        effective=_is_effective(state),
        warning_type=_warning_for(payload),
        vision_metadata_json=payload.visionMetadata or {},
    )
    db.add(log)
    db.flush()
    stats = _calculate_stats(session, now())
    _apply_stats(session, stats)
    db.commit()
    db.refresh(log)
    db.refresh(session)
    return {"stateLog": state_log_out(log), "session": session_out(session, live=True)}


def analyze_frame(db: Session, current_user: User, payload: FocusFrameAnalyzeRequest, image_bytes: bytes | None = None) -> dict:
    session = get_session_or_404(db, payload.sessionId, current_user)
    if session.status != "active":
        raise AppException("学习 session 已结束，不能继续分析画面", 400)
    return analyze_focus_frame(payload, image_bytes=image_bytes)


def end_session(db: Session, current_user: User, session_id: int) -> dict:
    session = get_session_or_404(db, session_id, current_user)
    if session.status == "completed":
        return session_out(session)
    session.end_time = now()
    session.status = "completed"
    stats = _calculate_stats(session, session.end_time)
    _apply_stats(session, stats)
    db.commit()
    db.refresh(session)
    return session_out(session)
