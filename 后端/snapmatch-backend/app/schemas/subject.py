from app.schemas.common import CamelModel


class SubjectCreateRequest(CamelModel):
    name: str
    description: str = ""


class SubjectUpdateRequest(CamelModel):
    name: str | None = None
    description: str | None = None


class SubjectOut(CamelModel):
    id: int
    name: str
    description: str
    createdAt: str
