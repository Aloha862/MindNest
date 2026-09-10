from app.schemas.common import CamelModel


class MaterialUpdateRequest(CamelModel):
    title: str | None = None
    category: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    remark: str | None = None


class MaterialOut(CamelModel):
    id: int
    fileId: int | None
    taskId: int | None
    userId: int
    title: str
    category: str
    summary: str
    tags: list[str]
    remark: str
    sourceImageUrl: str
    ocrSummary: str
    createdAt: str
    updatedAt: str
