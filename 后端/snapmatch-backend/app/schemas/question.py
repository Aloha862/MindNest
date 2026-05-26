from app.schemas.common import CamelModel


class QuestionBase(CamelModel):
    title: str
    content: str
    subject: str = "其他"
    questionType: str = "未知"
    knowledgePoints: list[str] = []
    options: list[str] = []
    formulas: list[dict] = []
    confidence: float = 0.0
    detailedAnalysis: str = ""
    solutionSteps: list[str] = []
    commonMistakes: list[str] = []
    errorCauseTags: list[str] = []
    reviewPlan: list[str] = []
    similarPracticeSuggestions: list[str] = []
    estimatedTime: str = ""
    reviewStatus: str = "approved"
    difficulty: str = "基础"
    answer: str = ""
    analysisSummary: str = ""
    sourceImageUrl: str = ""


class QuestionCreateRequest(QuestionBase):
    taskId: int | None = None
    fileId: int | None = None


class QuestionUpdateRequest(CamelModel):
    title: str | None = None
    content: str | None = None
    subject: str | None = None
    questionType: str | None = None
    knowledgePoints: list[str] | None = None
    options: list[str] | None = None
    formulas: list[dict] | None = None
    confidence: float | None = None
    detailedAnalysis: str | None = None
    solutionSteps: list[str] | None = None
    commonMistakes: list[str] | None = None
    errorCauseTags: list[str] | None = None
    reviewPlan: list[str] | None = None
    similarPracticeSuggestions: list[str] | None = None
    estimatedTime: str | None = None
    reviewStatus: str | None = None
    difficulty: str | None = None
    answer: str | None = None
    analysisSummary: str | None = None
    sourceImageUrl: str | None = None


class QuestionOut(QuestionBase):
    id: int
    taskId: int | None
    fileId: int | None
    userId: int
    isWrong: bool = False
    wrongRecord: dict | None = None
    createdAt: str
    updatedAt: str
