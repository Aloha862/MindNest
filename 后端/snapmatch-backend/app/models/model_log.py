from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class ModelLog(Base):
    __tablename__ = "model_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("recognition_tasks.id"), index=True, nullable=True)
    model_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), default="", index=True)
    error_code: Mapped[str] = mapped_column(String(64), default="", index=True)
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="success", index=True)
    cost_time: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    task = relationship("RecognitionTask", back_populates="logs")
