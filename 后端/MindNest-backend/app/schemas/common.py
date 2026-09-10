from pydantic import BaseModel, ConfigDict


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class PageQuery(CamelModel):
    keyword: str | None = None
    page: int = 1
    pageSize: int = 10


class IdResponse(CamelModel):
    id: int
