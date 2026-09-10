from pathlib import Path
from time import perf_counter

from sqlalchemy.orm import Session

from app.config import settings
from app.services.model_log_service import create_model_log
from app.utils.file_utils import path_to_upload_url


LABELS_CN = {
    "question": "题目区域",
    "stem": "题干",
    "sub_question": "小问",
    "option": "选项",
    "formula": "公式",
    "analysis": "分析解析",
    "answer": "答案",
    "diagram": "图表",
    "table": "表格",
    "handwriting": "手写批注",
}


LABELS_CN = {
    "question": "完整题目",
    "diagram": "图表",
    "formula": "公式/代码",
    "answer": "答案",
    "analysis": "解析",
}
ACTIVE_LABELS = set(LABELS_CN)


def get_yolo_model_name() -> str:
    if not settings.yolo_enabled:
        return "yolo-disabled"
    if settings.yolo_mode.lower() == "real":
        return f"ultralytics:{Path(settings.yolo_model_path).name}"
    return "opencv-layout-fallback-v1"


def _read_image(image_path: str):
    import cv2
    import numpy as np

    image_data = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("图片读取失败")
    return cv2, image


def _save_crop(image, source: Path, box: dict, label: str, index: int) -> str:
    import cv2

    output_dir = settings.upload_root / "processed" / "yolo"
    output_dir.mkdir(parents=True, exist_ok=True)
    x, y, width, height = box["x"], box["y"], box["width"], box["height"]
    crop = image[max(0, y) : max(0, y + height), max(0, x) : max(0, x + width)]
    if crop.size == 0:
        return ""
    output_path = output_dir / f"{source.stem}_{index:02d}_{label}.png"
    success, encoded = cv2.imencode(".png", crop)
    if not success:
        return ""
    encoded.tofile(str(output_path))
    return path_to_upload_url(output_path)


def _quality_metrics(cv2, image) -> dict:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "brightness": round(brightness, 2),
        "blurScore": round(blur_score, 2),
        "warnings": [
            warning
            for warning in [
                "图片偏暗" if brightness < 80 else "",
                "图片可能模糊" if blur_score < 80 else "",
            ]
            if warning
        ],
    }


def _safe_empty_result(mode: str, error_message: str = "") -> dict:
    return {
        "mode": mode,
        "imageWidth": 0,
        "imageHeight": 0,
        "detections": [],
        "layoutType": "unknown",
        "quality": {"warnings": [error_message] if error_message else []},
        "errorMessage": error_message,
    }


def _merge_boxes(boxes: list[dict], x_gap: int, y_gap: int) -> list[dict]:
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda item: (item["y"], item["x"]))
    merged: list[dict] = []
    for box in boxes:
        if not merged:
            merged.append(box)
            continue
        last = merged[-1]
        last_bottom = last["y"] + last["height"]
        box_bottom = box["y"] + box["height"]
        vertical_close = box["y"] <= last_bottom + y_gap
        horizontal_overlap = not (box["x"] > last["x"] + last["width"] + x_gap or last["x"] > box["x"] + box["width"] + x_gap)
        if vertical_close and horizontal_overlap:
            x1 = min(last["x"], box["x"])
            y1 = min(last["y"], box["y"])
            x2 = max(last["x"] + last["width"], box["x"] + box["width"])
            y2 = max(last_bottom, box_bottom)
            last.update({"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1})
        else:
            merged.append(box)
    return merged


def _detect_content_bands(cv2, image) -> list[dict]:
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(18, width // 28), max(3, height // 220)))
    dilated = cv2.dilate(binary, horizontal_kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < width * 0.08 or h < 8:
            continue
        if w * h < width * height * 0.001:
            continue
        pad_x = max(6, width // 120)
        pad_y = max(4, height // 160)
        boxes.append(
            {
                "x": max(0, x - pad_x),
                "y": max(0, y - pad_y),
                "width": min(width - max(0, x - pad_x), w + pad_x * 2),
                "height": min(height - max(0, y - pad_y), h + pad_y * 2),
            }
        )

    bands = _merge_boxes(boxes, x_gap=max(24, width // 20), y_gap=max(10, height // 80))
    return [box for box in bands if box["height"] < height * 0.85]


def _fallback_detect(image_path: str) -> dict:
    cv2, image = _read_image(image_path)
    source = Path(image_path)
    height, width = image.shape[:2]
    bands = _detect_content_bands(cv2, image)

    if not bands:
        bands = [
            {
                "x": int(width * 0.06),
                "y": int(height * 0.05),
                "width": int(width * 0.88),
                "height": int(height * 0.55),
            }
        ]

    detections = []
    for index, box in enumerate(bands[:10], start=1):
        if len(bands) == 1:
            label = "question"
        elif index == 1:
            label = "question"
        elif index == len(bands):
            label = "answer"
        else:
            label = "analysis"
        detections.append(
            {
                "label": label,
                "labelName": LABELS_CN[label],
                "confidence": 0.78,
                "bbox": box,
                "box": box,
                "cropUrl": _save_crop(image, source, box, label, index),
                "source": "opencv-fallback",
            }
        )

    question_count = sum(1 for item in detections if item["label"] == "question")
    return {
        "mode": "opencv-fallback",
        "imageWidth": width,
        "imageHeight": height,
        "detections": detections,
        "layoutType": "multi_question" if question_count > 1 or len(detections) > 5 else "single_question",
        "quality": _quality_metrics(cv2, image),
    }


def _real_detect(image_path: str) -> dict:
    from ultralytics import YOLO

    cv2, image = _read_image(image_path)
    source = Path(image_path)
    model_path = Path(settings.yolo_model_path)
    if not model_path.is_absolute():
        model_path = settings.project_root / model_path
    if not model_path.exists():
        raise FileNotFoundError(f"YOLO 权重不存在：{model_path}")

    model = YOLO(str(model_path))
    result = model(str(source), conf=settings.yolo_confidence, verbose=False)[0]
    names = result.names
    detections = []
    for index, item in enumerate(result.boxes, start=1):
        xyxy = item.xyxy[0].tolist()
        class_id = int(item.cls[0].item())
        label = str(names.get(class_id, class_id))
        if label not in ACTIVE_LABELS:
            continue
        x1, y1, x2, y2 = [int(value) for value in xyxy]
        box = {"x": x1, "y": y1, "width": max(0, x2 - x1), "height": max(0, y2 - y1)}
        detections.append(
            {
                "label": label,
                "labelName": LABELS_CN.get(label, label),
                "confidence": round(float(item.conf[0].item()), 4),
                "bbox": box,
                "box": box,
                "cropUrl": _save_crop(image, source, box, label, index),
                "source": "yolo",
            }
        )

    height, width = image.shape[:2]
    return {
        "mode": "real",
        "imageWidth": width,
        "imageHeight": height,
        "detections": detections,
        "layoutType": "multi_question" if sum(1 for item in detections if item["label"] == "question") > 1 else "single_question",
        "quality": _quality_metrics(cv2, image),
    }


def detect_layout(image_path: str, db: Session | None = None, task_id: int | None = None) -> dict:
    start = perf_counter()
    if not settings.yolo_enabled:
        result = {"mode": "off", "detections": [], "layoutType": "unknown", "quality": {}, "imageWidth": 0, "imageHeight": 0}
        if db:
            create_model_log(db, task_id=task_id, model_type="yolo", model_name="yolo-disabled", stage="yolo_running", output_summary="YOLO 已关闭")
        return result
    try:
        if settings.yolo_mode.lower() == "real":
            try:
                result = _real_detect(image_path)
                if not result.get("detections"):
                    result = _fallback_detect(image_path)
                    result["mode"] = "opencv-fallback-after-yolo-empty"
                    result["fallbackReason"] = "real-yolo-empty"
            except Exception as exc:
                result = _fallback_detect(image_path)
                result["mode"] = "opencv-fallback-after-yolo-failed"
                result["fallbackReason"] = str(exc)
        else:
            result = _fallback_detect(image_path)
        cost = int((perf_counter() - start) * 1000)
        if db:
            create_model_log(
                db,
                task_id=task_id,
                model_type="yolo",
                model_name=get_yolo_model_name(),
                stage="yolo_running",
                input_summary=image_path,
                output_summary=f"检测到 {len(result.get('detections', []))} 个视觉区域",
                status="success",
                cost_time=cost,
            )
        return result
    except Exception as exc:
        fallback = _safe_empty_result("failed", str(exc))
        cost = int((perf_counter() - start) * 1000)
        if db:
            create_model_log(
                db,
                task_id=task_id,
                model_type="yolo",
                model_name=get_yolo_model_name(),
                stage="yolo_running",
                error_code="LAYOUT_FAILED",
                input_summary=image_path,
                output_summary="YOLO/版面检测调用失败",
                status="failed",
                cost_time=cost,
                error_message=str(exc),
            )
        return fallback
