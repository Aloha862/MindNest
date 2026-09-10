from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_compat_schema()


def ensure_compat_schema() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "recognition_tasks" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("recognition_tasks")}
        if "ocr_formula_blocks" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE recognition_tasks ADD COLUMN ocr_formula_blocks TEXT NULL"))
                connection.execute(text("UPDATE recognition_tasks SET ocr_formula_blocks = '[]' WHERE ocr_formula_blocks IS NULL OR ocr_formula_blocks = ''"))
        if "yolo_result" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE recognition_tasks ADD COLUMN yolo_result TEXT NULL"))
                connection.execute(text("UPDATE recognition_tasks SET yolo_result = '{}' WHERE yolo_result IS NULL OR yolo_result = ''"))
        additions = {
            "batch_id": "VARCHAR(64) NOT NULL DEFAULT ''",
            "batch_order": "INT NOT NULL DEFAULT 0",
            "trace_id": "VARCHAR(64) NOT NULL DEFAULT ''",
            "error_code": "VARCHAR(64) NOT NULL DEFAULT ''",
            "error_stage": "VARCHAR(32) NOT NULL DEFAULT ''",
            "retry_count": "INT NOT NULL DEFAULT 0",
            "started_at": "DATETIME NULL",
            "heartbeat_at": "DATETIME NULL",
            "pipeline_options_json": "JSON NULL",
            "quality_json": "JSON NULL",
            "normalized_result_json": "JSON NULL",
        }
        with engine.begin() as connection:
            for name, ddl in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE recognition_tasks ADD COLUMN {name} {ddl}"))
            connection.execute(text("UPDATE recognition_tasks SET trace_id = '' WHERE trace_id IS NULL"))
            connection.execute(text("UPDATE recognition_tasks SET batch_id = '' WHERE batch_id IS NULL"))
            connection.execute(text("UPDATE recognition_tasks SET error_code = '' WHERE error_code IS NULL"))
            connection.execute(text("UPDATE recognition_tasks SET error_stage = '' WHERE error_stage IS NULL"))
            connection.execute(text("UPDATE recognition_tasks SET pipeline_options_json = JSON_OBJECT() WHERE pipeline_options_json IS NULL"))
            connection.execute(text("UPDATE recognition_tasks SET quality_json = JSON_OBJECT() WHERE quality_json IS NULL"))
            connection.execute(text("UPDATE recognition_tasks SET normalized_result_json = JSON_OBJECT() WHERE normalized_result_json IS NULL"))

    if "model_logs" in table_names:
        columns = {column["name"] for column in inspector.get_columns("model_logs")}
        additions = {
            "stage": "VARCHAR(32) NOT NULL DEFAULT ''",
            "error_code": "VARCHAR(64) NOT NULL DEFAULT ''",
            "metadata_json": "JSON NULL",
        }
        with engine.begin() as connection:
            for name, ddl in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE model_logs ADD COLUMN {name} {ddl}"))
            connection.execute(text("UPDATE model_logs SET stage = '' WHERE stage IS NULL"))
            connection.execute(text("UPDATE model_logs SET error_code = '' WHERE error_code IS NULL"))
            connection.execute(text("UPDATE model_logs SET metadata_json = JSON_OBJECT() WHERE metadata_json IS NULL"))

    if "questions" in table_names:
        columns = {column["name"] for column in inspector.get_columns("questions")}
        additions = {
            "options_json": "JSON NULL",
            "knowledge_points_json": "JSON NULL",
            "formulas_json": "JSON NULL",
            "raw_vlm_json": "JSON NULL",
            "source_bbox_json": "JSON NULL",
            "confidence": "DOUBLE NOT NULL DEFAULT 0",
            "review_status": "VARCHAR(32) NOT NULL DEFAULT 'approved'",
        }
        with engine.begin() as connection:
            for name, ddl in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE questions ADD COLUMN {name} {ddl}"))
            connection.execute(text("UPDATE questions SET options_json = JSON_ARRAY() WHERE options_json IS NULL"))
            connection.execute(text("UPDATE questions SET knowledge_points_json = JSON_ARRAY() WHERE knowledge_points_json IS NULL"))
            connection.execute(text("UPDATE questions SET formulas_json = JSON_ARRAY() WHERE formulas_json IS NULL"))
            connection.execute(text("UPDATE questions SET raw_vlm_json = JSON_OBJECT() WHERE raw_vlm_json IS NULL"))
            connection.execute(text("UPDATE questions SET source_bbox_json = JSON_OBJECT() WHERE source_bbox_json IS NULL"))
            connection.execute(text("UPDATE questions SET review_status = 'approved' WHERE review_status IS NULL OR review_status = ''"))

    if "upload_files" in table_names:
        columns = {column["name"] for column in inspector.get_columns("upload_files")}
        additions = {
            "batch_id": "VARCHAR(64) NOT NULL DEFAULT ''",
            "batch_order": "INT NOT NULL DEFAULT 0",
        }
        with engine.begin() as connection:
            for name, ddl in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE upload_files ADD COLUMN {name} {ddl}"))
            connection.execute(text("UPDATE upload_files SET batch_id = '' WHERE batch_id IS NULL"))

    if "study_state_logs" in table_names:
        columns = {column["name"] for column in inspector.get_columns("study_state_logs")}
        if "vision_metadata_json" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE study_state_logs ADD COLUMN vision_metadata_json JSON NULL"))
                connection.execute(text("UPDATE study_state_logs SET vision_metadata_json = JSON_OBJECT() WHERE vision_metadata_json IS NULL"))
