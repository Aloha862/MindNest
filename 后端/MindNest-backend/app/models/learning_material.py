from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class LearningMaterial(Base):
    __tablename__ = "learning_materials"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    file_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("upload_files.id"), index=True, nullable=True)
    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("recognition_tasks.id"), index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="note", index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="[]")
    remark: Mapped[str] = mapped_column(Text, default="")
    source_image_url: Mapped[str] = mapped_column(String(500), default="")
    ocr_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="materials")
    file = relationship("UploadFile", back_populates="materials")
    task = relationship("RecognitionTask", back_populates="materials")
