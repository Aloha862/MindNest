from app.schemas.common import CamelModel


class FileOut(CamelModel):
    id: int
    userId: int
    userName: str
    fileName: str
    fileType: str
    batchId: str = ""
    batchOrder: int = 0
    fileUrl: str
    originalImageUrl: str
    preprocessImageUrl: str
    size: int
    status: str
    remark: str
    createdAt: str
    updatedAt: str
