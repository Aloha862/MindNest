from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class RecognitionTask(Base):
    __tablename__ = "recognition_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("upload_files.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    batch_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    batch_order: Mapped[int] = mapped_column(Integer, default=0)
    trace_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    status: Mapped[str] = mapped_column(default="pending", index=True)
    current_step: Mapped[str] = mapped_column(default="等待识别")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(64), default="", index=True)
    error_stage: Mapped[str] = mapped_column(String(32), default="", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    ocr_text: Mapped[str] = mapped_column(Text, default="")
    ocr_blocks: Mapped[str] = mapped_column(Text, default="[]")
    ocr_formula_blocks: Mapped[str] = mapped_column(Text, default="[]")
    yolo_result: Mapped[str] = mapped_column(Text, default="{}")
    vlm_summary: Mapped[str] = mapped_column(Text, default="")
    vlm_result: Mapped[str] = mapped_column(Text, default="{}")
    pipeline_options_json: Mapped[dict] = mapped_column(JSON, default=dict)
    quality_json: Mapped[dict] = mapped_column(JSON, default=dict)
    normalized_result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    file = relationship("UploadFile", back_populates="tasks")
    user = relationship("User", back_populates="tasks")
    questions = relationship("Question", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("ModelLog", back_populates="task", cascade="all, delete-orphan")
    materials = relationship("LearningMaterial", back_populates="task", cascade="all, delete-orphan")
