from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.exceptions import register_exception_handlers
from app.routers import admin, auth, export, file, material, question, recognition, subject, user, wrong_record
from app.utils.file_utils import ensure_upload_dirs


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/docs", redoc_url="/redoc")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    ensure_upload_dirs()
    app.mount("/uploads", StaticFiles(directory=str(settings.upload_root)), name="uploads")

    @app.on_event("startup")
    def on_startup() -> None:
        Path(settings.upload_root).mkdir(parents=True, exist_ok=True)
        init_db()
        logger.info(
            "SnapMatch config loaded: OCR_PROVIDER=%s, PADDLEOCR_ENABLED=%s, VLM_PROVIDER=%s, VLM_MODEL=%s",
            settings.ocr_provider,
            settings.paddleocr_enabled,
            settings.vlm_provider,
            settings.vlm_model_name,
        )

    @app.get("/api/health", tags=["健康检查"])
    def health():
        return {"status": "ok", "project": "SnapMatch Backend"}

    app.include_router(auth.router, prefix="/api")
    app.include_router(user.router, prefix="/api")
    app.include_router(file.router, prefix="/api")
    app.include_router(recognition.router, prefix="/api")
    app.include_router(question.router, prefix="/api")
    app.include_router(subject.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(export.router, prefix="/api")
    app.include_router(wrong_record.router, prefix="/api")
    app.include_router(material.router, prefix="/api")
    return app


app = create_app()
