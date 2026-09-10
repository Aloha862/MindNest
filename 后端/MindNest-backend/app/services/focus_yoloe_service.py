import base64
import binascii
from functools import lru_cache
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any

from app.config import settings
from app.schemas.focus import FocusFrameAnalyzeRequest


LABEL_NAMES = {
    "person": "人体",
    "mobile phone": "手机",
    "smartphone": "手机",
    "phone": "手机",
    "cell phone": "手机",
    "handheld phone": "手机",
    "mobile device": "手机",
    "book": "书本",
    "open book": "书本",
    "laptop": "笔记本电脑",
    "computer monitor": "显示器",
    "monitor": "显示器",
    "keyboard": "键盘",
    "pen": "笔",
    "pencil": "笔",
    "notebook": "笔记本",
}
PHONE_LABELS = {"mobile phone", "phone", "cell phone", "smartphone", "handheld phone", "mobile device"}
COMPUTER_LABELS = {"laptop", "computer monitor", "monitor"}
STUDY_LABELS = {"book", "open book", "notebook", "pen", "pencil", "keyboard"}
BLOCKING_CLIENT_STATES = {"away", "bad_posture", "fatigue"}
MODEL_LOCK = Lock()


def _classes() -> list[str]:
    return [item.strip() for item in settings.focus_yoloe_classes.split(",") if item.strip()]


def _model_display_name() -> str:
    return f"yoloe-26m:{Path(settings.focus_yoloe_model).name}"


def _unavailable(reason: str, latency_ms: int = 0) -> dict:
    return {
        "available": False,
        "modelName": _model_display_name(),
        "latencyMs": latency_ms,
        "detections": [],
        "detectedObjects": [],
        "suggestedState": "unknown",
        "suggestedFocusScore": 0,
        "warningType": "",
        "reason": reason,
    }


def _decode_raw_image(raw: bytes) -> Any:
    import cv2
    import numpy as np

    buffer = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("图片帧解码失败")
    return image


def _decode_image(image_data: str, image_bytes: bytes | None = None) -> tuple[Any, int]:
    if image_bytes is not None:
        if len(image_bytes) > settings.focus_yoloe_max_frame_bytes:
            raise ValueError("图片帧超过后端抽帧大小限制")
        return _decode_raw_image(image_bytes), len(image_bytes)

    if "," in image_data and image_data.strip().lower().startswith("data:image"):
        image_data = image_data.split(",", 1)[1]
    try:
        raw = base64.b64decode(image_data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("图片帧不是合法 base64 数据") from exc

    if len(raw) > settings.focus_yoloe_max_frame_bytes:
        raise ValueError("图片帧超过后端抽帧大小限制")

    return _decode_raw_image(raw), len(raw)


@lru_cache(maxsize=1)
def _load_model():
    from ultralytics import YOLOE

    model_path = Path(settings.focus_yoloe_model)
    source = str(model_path if model_path.is_absolute() else settings.focus_yoloe_model)
    model = YOLOE(source)
    classes = _classes()
    try:
        model.set_classes(classes)
    except TypeError:
        model.set_classes(classes, model.get_text_pe(classes))
    return model


def _resolve_device() -> str:
    configured = settings.focus_yoloe_device.strip()
    if configured:
        return configured

    try:
        import torch

        return "0" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _predict(model, image: Any):
    kwargs: dict[str, Any] = {
        "source": image,
        "conf": settings.focus_yoloe_confidence,
        "imgsz": settings.focus_yoloe_imgsz,
        "verbose": False,
        "device": _resolve_device(),
    }
    try:
        return model.predict(**kwargs)[0], kwargs["device"]
    except Exception:
        if kwargs["device"] == "cpu":
            raise
        kwargs["device"] = "cpu"
        return model.predict(**kwargs)[0], "cpu"


def _normalize_label(label: str) -> str:
    normalized = str(label or "").strip().lower()
    aliases = {
        "cell phone": "mobile phone",
        "phone": "mobile phone",
        "smartphone": "mobile phone",
        "handheld phone": "mobile phone",
        "mobile device": "mobile phone",
        "monitor": "computer monitor",
        "open book": "book",
        "pencil": "pen",
    }
    return aliases.get(normalized, normalized)


def _area_ratio(detection: dict) -> float:
    box = detection.get("bbox") or {}
    image_width = max(1, int(detection.get("imageWidth") or 1))
    image_height = max(1, int(detection.get("imageHeight") or 1))
    return (max(0, int(box.get("width") or 0)) * max(0, int(box.get("height") or 0))) / (image_width * image_height)


def _keep_detection(detection: dict) -> bool:
    label = detection.get("label")
    confidence = float(detection.get("confidence") or 0)
    area = _area_ratio(detection)
    box = detection.get("bbox") or {}
    width = max(1, int(box.get("width") or 1))
    height = max(1, int(box.get("height") or 1))
    aspect = width / height

    if label == "mobile phone":
        return confidence >= 0.5 or (confidence >= 0.45 and area >= 0.006)
    if label == "laptop":
        return confidence >= 0.45 and area >= 0.025
    if label == "computer monitor":
        return confidence >= 0.35 and area >= 0.03
    if label == "person":
        return confidence >= 0.5 and area >= 0.01
    if label in {"book", "keyboard"}:
        return confidence >= 0.3 and area >= 0.015
    if label == "pen":
        return confidence >= 0.35 and 0.15 <= aspect <= 8.0
    return confidence >= 0.3


def _bbox_iou(left: dict, right: dict) -> float:
    left_box = left.get("bbox") or {}
    right_box = right.get("bbox") or {}
    ax1 = float(left_box.get("x") or 0)
    ay1 = float(left_box.get("y") or 0)
    ax2 = ax1 + float(left_box.get("width") or 0)
    ay2 = ay1 + float(left_box.get("height") or 0)
    bx1 = float(right_box.get("x") or 0)
    by1 = float(right_box.get("y") or 0)
    bx2 = bx1 + float(right_box.get("width") or 0)
    by2 = by1 + float(right_box.get("height") or 0)

    inter_width = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_height = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter_area = inter_width * inter_height
    left_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    right_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = left_area + right_area - inter_area
    return inter_area / union_area if union_area else 0.0


def _dedupe_detections(detections: list[dict]) -> list[dict]:
    kept: list[dict] = []
    for detection in sorted(detections, key=lambda item: float(item.get("confidence") or 0), reverse=True):
        if any(detection.get("label") == item.get("label") and _bbox_iou(detection, item) >= 0.5 for item in kept):
            continue
        kept.append(detection)
    return kept


def _detections_from_result(result) -> list[dict]:
    names = getattr(result, "names", {}) or {}
    boxes = getattr(result, "boxes", None)
    detections = []
    if boxes is None:
        return detections
    image_height, image_width = getattr(result, "orig_shape", (0, 0)) or (0, 0)

    for item in boxes:
        xyxy = item.xyxy[0].tolist()
        class_id = int(item.cls[0].item())
        label = _normalize_label(names.get(class_id, class_id))
        confidence = round(float(item.conf[0].item()), 4)
        x1, y1, x2, y2 = [int(value) for value in xyxy]
        detection = {
            "label": label,
            "labelName": LABEL_NAMES.get(label, label),
            "confidence": confidence,
            "bbox": {"x": x1, "y": y1, "width": max(0, x2 - x1), "height": max(0, y2 - y1)},
            "imageWidth": int(image_width),
            "imageHeight": int(image_height),
            "source": "yoloe-26m",
        }
        if _keep_detection(detection):
            detections.append(detection)
    return _dedupe_detections(detections)


def _fuse(payload: FocusFrameAnalyzeRequest, detections: list[dict]) -> dict:
    labels = {item["label"] for item in detections}
    detected_objects = sorted(labels)
    has_person = "person" in labels
    has_phone = bool(labels & PHONE_LABELS)
    has_computer = bool(labels & COMPUTER_LABELS)
    has_study_object = bool(labels & STUDY_LABELS)

    client_state = payload.clientState or "unknown"
    suggested_state = client_state
    warning_type = ""
    score = max(0, min(100, int(payload.clientFocusScore or 0)))
    reason = "沿用端侧姿态结果"

    if client_state == "away":
        suggested_state = "away"
        score = min(score, 10)
        warning_type = "away"
        reason = "端侧识别为离座，后端对象检测不强行改回专注"
    elif client_state in {"bad_posture", "fatigue"}:
        suggested_state = client_state
        warning_type = "fatigue" if client_state == "fatigue" else "posture"
        reason = "姿态异常仍以端侧识别为主，YOLOE 只补充对象证据"
    elif has_phone:
        suggested_state = "distracted_phone"
        score = max(0, score - 20)
        warning_type = "phone"
        reason = "YOLOE 检测到手机进入学习画面"
    elif has_person and has_computer:
        suggested_state = "computer_learning"
        score = min(100, score + 5)
        reason = "YOLOE 检测到电脑或显示器，辅助判定为看电脑学习"
    elif has_person and has_study_object and client_state in {"focused", "writing", "unknown"}:
        suggested_state = "writing" if client_state == "writing" else "focused"
        score = min(100, score + 5)
        reason = "YOLOE 检测到书本/笔/键盘等学习物品"
    elif not has_person and client_state not in BLOCKING_CLIENT_STATES:
        suggested_state = client_state
        reason = "YOLOE 未检测到人体，等待端侧连续姿态确认"

    return {
        "detectedObjects": detected_objects,
        "suggestedState": suggested_state,
        "suggestedFocusScore": score,
        "warningType": warning_type,
        "reason": reason,
    }


def analyze_focus_frame(payload: FocusFrameAnalyzeRequest, image_bytes: bytes | None = None) -> dict:
    start = perf_counter()
    if not settings.focus_yoloe_enabled:
        return _unavailable("YOLOE 专注识别已关闭")

    try:
        image, frame_bytes = _decode_image(payload.imageData, image_bytes=image_bytes)
        with MODEL_LOCK:
            model = _load_model()
            result, device = _predict(model, image)
        detections = _detections_from_result(result)
        latency_ms = int((perf_counter() - start) * 1000)
        fused = _fuse(payload, detections)
        return {
            "available": True,
            "modelName": _model_display_name(),
            "device": device,
            "latencyMs": latency_ms,
            "detections": detections,
            "frameBytes": frame_bytes,
            **fused,
        }
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown"
        if missing == "ultralytics":
            reason = "未安装 ultralytics，请在后端虚拟环境安装后重试"
        elif missing == "clip":
            reason = "未安装 YOLOE 文本提示依赖 CLIP，请按 README 安装后重试"
        else:
            reason = f"YOLOE 依赖缺失：{missing}"
        return _unavailable(reason, int((perf_counter() - start) * 1000))
    except ImportError as exc:
        return _unavailable(f"YOLOE 依赖加载失败：{exc}", int((perf_counter() - start) * 1000))
    except Exception as exc:
        return _unavailable(str(exc), int((perf_counter() - start) * 1000))


def warmup_focus_yoloe() -> dict:
    if not settings.focus_yoloe_enabled:
        return _unavailable("YOLOE 专注识别已关闭")

    import cv2
    import numpy as np

    image = np.full((settings.focus_yoloe_imgsz, settings.focus_yoloe_imgsz, 3), 245, dtype=np.uint8)
    ok, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if not ok:
        raise ValueError("YOLOE 预热图片编码失败")

    payload = FocusFrameAnalyzeRequest(
        sessionId=0,
        imageData="",
        clientState="away",
        clientFocusScore=0,
        clientPosture="away",
    )
    return analyze_focus_frame(payload, image_bytes=buffer.tobytes())
