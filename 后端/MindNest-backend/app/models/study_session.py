from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="学习专注")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)
    total_duration: Mapped[int] = mapped_column(Integer, default=0)
    effective_duration: Mapped[int] = mapped_column(Integer, default=0)
    distraction_count: Mapped[int] = mapped_column(Integer, default=0)
    away_count: Mapped[int] = mapped_column(Integer, default=0)
    phone_duration: Mapped[int] = mapped_column(Integer, default=0)
    posture_warning_count: Mapped[int] = mapped_column(Integer, default=0)
    average_focus_score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    user = relationship("User", back_populates="study_sessions")
    state_logs = relationship("StudyStateLog", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("StudyReport", back_populates="session", cascade="all, delete-orphan")
