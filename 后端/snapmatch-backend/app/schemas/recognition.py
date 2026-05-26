from app.schemas.common import CamelModel


class RecognitionStartRequest(CamelModel):
    fileId: int
    enablePreprocess: bool = True
    enableYOLO: bool = True
    enableOCR: bool = True
    enableVLM: bool = True


class RecognitionBatchStartRequest(CamelModel):
    fileIds: list[int]
    enablePreprocess: bool = True
    enableYOLO: bool = True
    enableOCR: bool = True
    enableVLM: bool = True


class RecognitionTaskOut(CamelModel):
    id: int
    fileId: int
    fileName: str
    userId: int
    userName: str
    batchId: str = ""
    batchOrder: int = 0
    traceId: str = ""
    status: str
    currentStep: str
    progress: int
    errorCode: str = ""
    errorStage: str = ""
    retryCount: int = 0
    qualityWarnings: list[str] = []
    questionCount: int
    ocrText: str = ""
    vlmSummary: str = ""
    errorMessage: str = ""
    createdAt: str
    updatedAt: str
    startedAt: str
    heartbeatAt: str
    finishedAt: str


class RecognitionProgressOut(CamelModel):
    taskId: int
    status: str
    currentStep: str
    progress: int
    message: str


class OCRResultOut(CamelModel):
    rawText: str
    blocks: list[dict]
    formulaBlocks: list[dict] = []
    mergedBlocks: list[dict] = []
    mergedText: str = ""
    quality: dict = {}
    sections: list[dict] = []
    layoutBlocks: list[dict] = []
    yolo: dict = {}
    originalImageUrl: str
    preprocessImageUrl: str


class VLMResultOut(CamelModel):
    summary: str
    questions: list[dict]
    normalized: dict = {}
    needsReview: bool = False
    validationWarnings: list[str] = []
