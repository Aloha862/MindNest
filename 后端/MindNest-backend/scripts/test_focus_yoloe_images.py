"""Run YOLOE focus-object regression checks on realistic study-scene images.

The script encodes each input like the frontend webcam sampler, invokes the
same backend service used by /api/focus/analyze-frame, and writes annotated
images plus a JSON report under tests/focus_yoloe/output.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from time import perf_counter

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings
from app.schemas.focus import FocusFrameAnalyzeRequest
from app.services.focus_yoloe_service import analyze_focus_frame


INPUT_DIR = ROOT / "tests" / "focus_yoloe" / "input"
OUTPUT_DIR = ROOT / "tests" / "focus_yoloe" / "output"
MANIFEST_PATH = ROOT / "tests" / "focus_yoloe" / "manifest.json"
DISPLAY_LABELS = {
    "person": "person",
    "mobile phone": "mobile phone",
    "book": "book",
    "laptop": "laptop",
    "computer monitor": "monitor",
    "keyboard": "keyboard",
    "pen": "pen",
    "notebook": "notebook",
}


def expected_hit(expected_item, detected: list[str]) -> bool:
    if isinstance(expected_item, list):
        return any(label in detected for label in expected_item)
    return expected_item in detected


def expected_name(expected_item) -> str:
    if isinstance(expected_item, list):
        return " / ".join(str(item) for item in expected_item)
    return str(expected_item)


def read_image(path: Path) -> np.ndarray:
    """Decode paths containing non-ASCII characters reliably on Windows."""
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to decode image: {path}")
    return image


def expected_labels(expected: list) -> set[str]:
    labels: set[str] = set()
    for item in expected:
        if isinstance(item, list):
            labels.update(str(label) for label in item)
        else:
            labels.add(str(item))
    return labels


def encode_camera_frame(image: np.ndarray) -> tuple[np.ndarray, bytes]:
    """Mirror FocusMonitor.vue frame scaling and PNG frame encoding."""
    height, width = image.shape[:2]
    max_edge = settings.focus_yoloe_imgsz
    scale = min(1.0, max_edge / max(width, height))
    resized = cv2.resize(
        image,
        (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )
    ok, buffer = cv2.imencode(".png", resized, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
    if not ok:
        raise ValueError("Unable to encode camera-style PNG frame")
    return resized, buffer.tobytes()


def annotate(image: np.ndarray, detections: list[dict], output_path: Path) -> None:
    canvas = image.copy()
    colors = {"mobile phone": (30, 30, 232), "person": (60, 180, 70)}
    for item in detections:
        box = item.get("bbox") or {}
        x = int(box.get("x", 0))
        y = int(box.get("y", 0))
        width = int(box.get("width", 0))
        height = int(box.get("height", 0))
        label = str(item.get("label", "object"))
        confidence = float(item.get("confidence", 0))
        color = colors.get(label, (238, 126, 34))
        cv2.rectangle(canvas, (x, y), (x + width, y + height), color, 2)
        caption = f"{DISPLAY_LABELS.get(label, label)} {confidence:.2f}"
        label_y = max(20, y - 8)
        cv2.putText(canvas, caption, (x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, color, 2)
    ok, buffer = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        raise ValueError(f"Unable to encode annotated output: {output_path}")
    buffer.tofile(str(output_path))


def run_case(image_path: Path, expected: list[str]) -> dict:
    image = read_image(image_path)
    frame, frame_bytes = encode_camera_frame(image)
    payload = FocusFrameAnalyzeRequest(
        sessionId=0,
        imageData="",
        clientState="focused",
        clientConfidence=0.96,
        clientPosture="normal",
        clientFocusScore=90,
    )
    start = perf_counter()
    result = analyze_focus_frame(payload, image_bytes=frame_bytes)
    elapsed_ms = int((perf_counter() - start) * 1000)
    detected = result.get("detectedObjects", [])
    missing = [expected_name(label) for label in expected if not expected_hit(label, detected)]
    extra = [label for label in detected if label not in expected_labels(expected)]
    annotate(frame, result.get("detections", []), OUTPUT_DIR / f"{image_path.stem}_detected.jpg")
    return {
        "file": image_path.name,
        "expected": expected,
        "detected": detected,
        "missing": missing,
        "extra": extra,
        "passed": result.get("available", False) and not missing,
        "available": result.get("available", False),
        "reason": result.get("reason", ""),
        "latencyMs": result.get("latencyMs", elapsed_ms),
        "frameBytes": len(frame_bytes),
        "detections": result.get("detections", []),
        "annotatedImage": str(OUTPUT_DIR / f"{image_path.stem}_detected.jpg"),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [run_case(INPUT_DIR / name, expected) for name, expected in manifest.items()]
    report = {
        "model": settings.focus_yoloe_model,
        "confidence": settings.focus_yoloe_confidence,
        "imageSize": settings.focus_yoloe_imgsz,
        "classes": settings.focus_yoloe_classes.split(","),
        "cases": rows,
        "summary": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row["passed"]),
            "failed": sum(1 for row in rows if not row["passed"]),
        },
    }
    report_path = OUTPUT_DIR / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    for row in rows:
        status = "PASS" if row["passed"] else "MISS"
        print(f"{status} {row['file']}: detected={row['detected']} missing={row['missing']} latency={row['latencyMs']}ms")
    print(f"report={report_path}")
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
