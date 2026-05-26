from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class WrongRecord(Base):
    __tablename__ = "wrong_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    file_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("upload_files.id"), index=True, nullable=True)
    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("recognition_tasks.id"), index=True, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    mastery_status: Mapped[str] = mapped_column(String(32), default="unreviewed", index=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_review_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    question = relationship("Question", back_populates="wrong_records")
    user = relationship("User", back_populates="wrong_records")
    attempts = relationship("WrongReviewAttempt", back_populates="wrong_record", cascade="all, delete-orphan")
