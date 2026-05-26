from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "SnapMatch Backend"
    app_env: str = "development"
    debug: bool = False

    database_url: str = "mysql+pymysql://root:password@127.0.0.1:3306/snapmatch?charset=utf8mb4"
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    upload_dir: str = "app/uploads"
    backend_base_url: str = "http://127.0.0.1:8000"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    max_upload_size: int = Field(default=10 * 1024 * 1024)

    ocr_provider: str = "mock"
    ocr_model_name: str = "qwen-vl-ocr-latest"
    paddleocr_enabled: bool = False
    vlm_provider: str = "mock"
    dashscope_api_key: str = ""
    vlm_api_key: str = ""
    vlm_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    vlm_model_name: str = "qwen3.6-plus"
    vlm_enable_thinking: bool = False
    vlm_stream: bool = False

    yolo_enabled: bool = True
    yolo_mode: str = "mock"
    yolo_model_path: str = "weights/best.pt"
    yolo_confidence: float = 0.35
    formula_provider: str = "pix2text"
    max_concurrent_recognition: int = 2
    vlm_json_repair_retry: int = 1

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def upload_root(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = self.project_root / path
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
