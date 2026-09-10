from app.schemas.common import CamelModel


class DailyReportOut(CamelModel):
    date: str
    content: str
    stats: dict
    recommendations: list[str]
    focusTrend: list[dict] = []
    weakKnowledgePoints: list[dict] = []
    errorCauseStats: list[dict] = []


class SessionReportOut(CamelModel):
    session: dict
    content: str
    stats: dict
    recommendations: list[str]
