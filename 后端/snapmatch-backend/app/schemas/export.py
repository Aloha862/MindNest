from app.schemas.common import CamelModel


class ExportRequest(CamelModel):
    range: str = "current"
    format: str = "markdown"
    keyword: str | None = None
    subject: str | None = None
    questionType: str | None = None
    difficulty: str | None = None
    taskId: int | None = None
    batchId: str | None = None
    knowledgePoint: str | None = None
    masteryStatus: str | None = None
    startTime: str | None = None
    endTime: str | None = None
