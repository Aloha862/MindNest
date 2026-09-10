from typing import Any

from pydantic import Field

from app.schemas.common import CamelModel


class FocusStartRequest(CamelModel):
    title: str = "学习专注"


class FocusStateRequest(CamelModel):
    sessionId: int
    state: str = "unknown"
    detectedObjects: list[str] = Field(default_factory=list)
    posture: str = ""
    focusScore: int = 0
    warningType: str = ""
    visionMetadata: dict[str, Any] = Field(default_factory=dict)


class FocusFrameAnalyzeRequest(CamelModel):
    sessionId: int
    imageData: str
    clientState: str = "unknown"
    clientConfidence: float = 0
    clientPosture: str = ""
    clientFocusScore: int = 0
    capturedAt: str = ""


class FocusEndRequest(CamelModel):
    sessionId: int


class FocusSessionOut(CamelModel):
    id: int
    title: str
    status: str
    startTime: str
    endTime: str
    totalDuration: int
    effectiveDuration: int
    distractionCount: int
    awayCount: int
    phoneDuration: int
    postureWarningCount: int
    averageFocusScore: int
    summary: str
    currentState: str = ""
    logs: list[dict] = Field(default_factory=list)


class FocusStateOut(CamelModel):
    id: int
    sessionId: int
    timestamp: str
    state: str
    detectedObjects: list[str]
    posture: str
    focusScore: int
    effective: bool
    warningType: str
    visionMetadata: dict[str, Any] = Field(default_factory=dict)
