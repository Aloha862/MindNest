from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class UploadFile(Base):
    __tablename__ = "upload_files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    batch_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    batch_order: Mapped[int] = mapped_column(default=0)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    processed_path: Mapped[str] = mapped_column(String(500), default="")
    size: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="files")
    tasks = relationship("RecognitionTask", back_populates="file", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="file", cascade="all, delete-orphan")
    materials = relationship("LearningMaterial", back_populates="file", cascade="all, delete-orphan")
