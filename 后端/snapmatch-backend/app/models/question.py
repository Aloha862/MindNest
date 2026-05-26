from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("recognition_tasks.id"), index=True, nullable=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("upload_files.id"), index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(String(64), index=True, default="其他")
    question_type: Mapped[str] = mapped_column(String(64), index=True, default="未知")
    knowledge_points: Mapped[str] = mapped_column(Text, default="[]")
    options_json: Mapped[list] = mapped_column(JSON, default=list)
    knowledge_points_json: Mapped[list] = mapped_column(JSON, default=list)
    formulas_json: Mapped[list] = mapped_column(JSON, default=list)
    raw_vlm_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_bbox_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    review_status: Mapped[str] = mapped_column(String(32), default="approved", index=True)
    difficulty: Mapped[str] = mapped_column(String(32), index=True, default="基础")
    answer: Mapped[str] = mapped_column(Text, default="")
    analysis_summary: Mapped[str] = mapped_column(Text, default="")
    source_image_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    task = relationship("RecognitionTask", back_populates="questions")
    file = relationship("UploadFile", back_populates="questions")
    user = relationship("User", back_populates="questions")
    wrong_records = relationship("WrongRecord", back_populates="question", cascade="all, delete-orphan")
