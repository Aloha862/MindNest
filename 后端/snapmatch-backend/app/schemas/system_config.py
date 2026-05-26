from app.schemas.common import CamelModel


class SystemConfigPayload(CamelModel):
    ocrEnabled: bool = True
    vlmEnabled: bool = True
    maxUploadSizeMb: int = 10
    allowedFileTypes: str = "jpg, jpeg, png"
    modelEndpoint: str = "http://127.0.0.1:8000/api"


class SystemConfigOut(SystemConfigPayload):
    backendEnabled: bool = True
