from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time_utils import now


class StudyStateLog(Base):
    __tablename__ = "study_state_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("study_sessions.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    state: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    detected_objects_json: Mapped[list] = mapped_column(JSON, default=list)
    vision_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    posture: Mapped[str] = mapped_column(String(64), default="")
    focus_score: Mapped[int] = mapped_column(Integer, default=0)
    effective: Mapped[bool] = mapped_column(Boolean, default=False)
    warning_type: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    session = relationship("StudySession", back_populates="state_logs")
    user = relationship("User", back_populates="study_state_logs")
