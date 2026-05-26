from app.schemas.common import CamelModel


class WrongRecordCreateRequest(CamelModel):
    note: str = ""
    masteryStatus: str = "unreviewed"
    source: str = "manual"


class WrongRecordUpdateRequest(CamelModel):
    note: str | None = None
    masteryStatus: str | None = None
    reviewCount: int | None = None
    increaseReviewCount: bool = False


class WrongReviewAttemptCreateRequest(CamelModel):
    result: str
    selfRating: str = "normal"
    note: str = ""


class WrongReviewAttemptOut(CamelModel):
    id: int
    wrongRecordId: int
    questionId: int
    userId: int
    result: str
    selfRating: str
    note: str
    createdAt: str


class WrongRecordOut(CamelModel):
    id: int
    questionId: int
    userId: int
    fileId: int | None
    taskId: int | None
    note: str
    masteryStatus: str
    reviewCount: int
    lastReviewTime: str
    attemptCount: int = 0
    latestAttempt: dict | None = None
    source: str
    question: dict | None = None
    createdAt: str
    updatedAt: str
