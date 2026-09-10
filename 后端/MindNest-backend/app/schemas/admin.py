from app.schemas.common import CamelModel


class AdminDashboardOut(CamelModel):
    userCount: int
    fileCount: int
    recognitionTaskCount: int
    questionCount: int
    todayUploadCount: int
    todayRecognitionCount: int
    taskStatusDistribution: list[dict]
    subjectDistribution: list[dict]
    modelLatency: list[dict] = []
    failureReasons: list[dict] = []
    stageFailureDistribution: list[dict] = []
    ocrEmptyCount: int = 0
    vlmInvalidJsonCount: int = 0
    recentLogs: list[dict]
    recentFiles: list[dict]
