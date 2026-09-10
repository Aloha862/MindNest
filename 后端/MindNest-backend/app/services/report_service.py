from collections import Counter
from datetime import datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.question import Question
from app.models.study_report import StudyReport
from app.models.study_session import StudySession
from app.models.user import User
from app.models.wrong_record import WrongRecord
from app.services.focus_service import _duration_text, session_out
from app.services.serializers import parse_json_dict, parse_json_list
from app.utils.response import page_data
from app.utils.time_utils import format_datetime, now


def _day_range(value: datetime | None = None) -> tuple[datetime, datetime]:
    current = value or now()
    start = datetime.combine(current.date(), time.min)
    end = datetime.combine(current.date(), time.max)
    return start, end


def _top(counter: Counter, limit: int = 5) -> list[dict]:
    return [{"name": name, "value": value} for name, value in counter.most_common(limit) if name]


def _question_insights(questions: list[Question]) -> tuple[list[dict], list[dict], list[str]]:
    knowledge = Counter()
    causes = Counter()
    plans: list[str] = []
    for question in questions:
        points = parse_json_list(question.knowledge_points_json) or parse_json_list(question.knowledge_points)
        knowledge.update(points)
        raw = parse_json_dict(question.raw_vlm_json)
        causes.update(parse_json_list(raw.get("errorCauseTags")))
        for item in parse_json_list(raw.get("reviewPlan")):
            if item and item not in plans:
                plans.append(item)
    return _top(knowledge), _top(causes), plans[:5]


def _build_content(stats: dict, weak_points: list[dict], causes: list[dict]) -> str:
    focus_rate = stats.get("focusEfficiency", 0)
    weak_text = "、".join(item["name"] for item in weak_points[:3]) or "暂无明显薄弱知识点"
    cause_text = "、".join(item["name"] for item in causes[:3]) or "暂无高频错因"
    return (
        f"今日共学习 {_duration_text(stats['totalDuration'])}，其中有效专注 "
        f"{_duration_text(stats['effectiveDuration'])}，专注效率 {focus_rate}%。"
        f"共沉淀题目 {stats['questionCount']} 道，错题 {stats['wrongCount']} 道。"
        f"当前主要薄弱点为：{weak_text}；主要错因集中在：{cause_text}。"
    )


def _recommendations(stats: dict, weak_points: list[dict], plans: list[str]) -> list[str]:
    result: list[str] = []
    if weak_points:
        result.append(f"优先复习 {weak_points[0]['name']}，再做 2-3 道同知识点练习。")
    if stats.get("phoneDuration", 0) >= 60:
        result.append("下一次学习前把手机移出视野，减少连续专注被打断。")
    if stats.get("awayCount", 0) > 0:
        result.append("把资料、水杯和草稿纸提前放好，降低学习中途离座。")
    result.extend(plans)
    if not result:
        result.append("保持当前节奏，下一次学习结束后继续生成复习报告。")
    return result[:6]


def daily_report(db: Session, current_user: User) -> dict:
    start, end = _day_range()
    sessions = db.scalars(
        select(StudySession)
        .where(StudySession.user_id == current_user.id, StudySession.start_time >= start, StudySession.start_time <= end)
        .order_by(StudySession.start_time.desc())
    ).all()
    questions = db.scalars(
        select(Question)
        .where(Question.user_id == current_user.id, Question.created_at >= start, Question.created_at <= end)
        .order_by(Question.created_at.desc())
    ).all()
    wrong_count = db.scalar(
        select(func.count(WrongRecord.id)).where(
            WrongRecord.user_id == current_user.id,
            WrongRecord.created_at >= start,
            WrongRecord.created_at <= end,
        )
    ) or 0
    weak_points, causes, plans = _question_insights(list(questions))
    total_duration = sum(item.total_duration for item in sessions)
    effective_duration = sum(item.effective_duration for item in sessions)
    stats = {
        "sessionCount": len(sessions),
        "totalDuration": total_duration,
        "effectiveDuration": effective_duration,
        "focusEfficiency": round(effective_duration / total_duration * 100) if total_duration else 0,
        "averageFocusScore": round(sum(item.average_focus_score for item in sessions) / len(sessions)) if sessions else 0,
        "distractionCount": sum(item.distraction_count for item in sessions),
        "awayCount": sum(item.away_count for item in sessions),
        "phoneDuration": sum(item.phone_duration for item in sessions),
        "questionCount": len(questions),
        "wrongCount": wrong_count,
    }
    content = _build_content(stats, weak_points, causes)
    recommendations = _recommendations(stats, weak_points, plans)
    report = db.scalars(
        select(StudyReport)
        .where(
            StudyReport.user_id == current_user.id,
            StudyReport.report_type == "daily",
            StudyReport.start_date == start,
        )
        .limit(1)
    ).first()
    if not report:
        report = StudyReport(user_id=current_user.id, report_type="daily", start_date=start, end_date=end)
        db.add(report)
    report.content = content
    report.stats_json = stats
    report.recommendations_json = recommendations
    report.end_date = end
    db.commit()
    return {
        "date": start.strftime("%Y-%m-%d"),
        "content": content,
        "stats": stats,
        "recommendations": recommendations,
        "focusTrend": [
            {
                "id": item.id,
                "title": item.title,
                "startTime": format_datetime(item.start_time),
                "effectiveDuration": item.effective_duration,
                "focusScore": item.average_focus_score,
            }
            for item in reversed(sessions[-8:])
        ],
        "weakKnowledgePoints": weak_points,
        "errorCauseStats": causes,
    }


def list_sessions(db: Session, current_user: User, page: int = 1, page_size: int = 10) -> dict:
    page = max(1, page)
    page_size = max(1, min(50, page_size))
    statement = select(StudySession).where(StudySession.user_id == current_user.id)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.scalars(statement.order_by(StudySession.start_time.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return page_data([session_out(item, include_logs=False) for item in rows], total, page, page_size)


def session_report(db: Session, current_user: User, session_id: int) -> dict:
    session = db.get(StudySession, session_id)
    if not session or session.user_id != current_user.id:
        raise AppException("学习 session 不存在", 404)
    start = session.start_time
    end = session.end_time or now()
    questions = db.scalars(
        select(Question).where(Question.user_id == current_user.id, Question.created_at >= start, Question.created_at <= end)
    ).all()
    wrong_count = db.scalar(
        select(func.count(WrongRecord.id)).where(
            WrongRecord.user_id == current_user.id,
            WrongRecord.created_at >= start,
            WrongRecord.created_at <= end,
        )
    ) or 0
    weak_points, causes, plans = _question_insights(list(questions))
    stats = {
        "questionCount": len(questions),
        "wrongCount": wrong_count,
        "focusEfficiency": round(session.effective_duration / session.total_duration * 100) if session.total_duration else 0,
        "totalDuration": session.total_duration,
        "effectiveDuration": session.effective_duration,
        "distractionCount": session.distraction_count,
        "awayCount": session.away_count,
        "phoneDuration": session.phone_duration,
        "averageFocusScore": session.average_focus_score,
    }
    content = (
        f"{session.title} 学习结束：有效专注 {_duration_text(session.effective_duration)}，"
        f"本次关联题目 {len(questions)} 道，错题 {wrong_count} 道。"
    )
    return {
        "session": session_out(session),
        "content": content,
        "stats": stats,
        "recommendations": _recommendations(stats, weak_points, plans),
        "weakKnowledgePoints": weak_points,
        "errorCauseStats": causes,
    }
