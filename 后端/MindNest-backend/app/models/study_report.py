from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class StudyReport(Base):
    __tablename__ = "study_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("study_sessions.id"), index=True, nullable=True)
    report_type: Mapped[str] = mapped_column(String(32), default="session", index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    stats_json: Mapped[dict] = mapped_column(JSON, default=dict)
    recommendations_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="study_reports")
    session = relationship("StudySession", back_populates="reports")
