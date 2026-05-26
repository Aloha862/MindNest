from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class WrongReviewAttempt(Base):
    __tablename__ = "wrong_review_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    wrong_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wrong_records.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), index=True, nullable=False)
    result: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    self_rating: Mapped[str] = mapped_column(String(32), default="normal", index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    wrong_record = relationship("WrongRecord", back_populates="attempts")
    user = relationship("User")
    question = relationship("Question")
