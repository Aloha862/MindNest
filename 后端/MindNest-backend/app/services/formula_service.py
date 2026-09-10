from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.services.model_log_service import create_model_log
from app.utils.file_utils import path_to_upload_url


FORMULA_MARKERS = (
    "=",
    "<=",
    ">=",
    "!=",
    "≤",
    "≥",
    "≠",
    "≈",
    "lim",
    "∫",
    "∑",
    "frac",
    "sin",
    "cos",
    "tan",
    "f(",
    "g(",
    "^",
    "²",
    "³",
)


@lru_cache
def _get_pix2text():
    if settings.formula_provider.lower() != "pix2text":
        return None
    try:
        from pix2text import Pix2Text
    except Exception:
        return None
    for factory in (
        lambda: Pix2Text.from_config(),
        lambda: Pix2Text(),
    ):
        try:
            return factory()
        except Exception:
            continue
    return None


def _bbox(block: dict | None) -> dict:
    if not isinstance(block, dict):
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    raw = block.get("bbox") or block.get("box") or {}
    if isinstance(raw, list):
        try:
            values = [float(item) for item in raw]
            if len(values) >= 4:
                x1, y1, x2, y2 = values[:4]
                return {"x": int(x1), "y": int(y1), "width": max(0, int(x2 - x1)), "height": max(0, int(y2 - y1))}
        except Exception:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
    if not isinstance(raw, dict):
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    return {
        "x": int(raw.get("x", 0) or 0),
        "y": int(raw.get("y", 0) or 0),
        "width": int(raw.get("width", 0) or 0),
        "height": int(raw.get("height", 0) or 0),
    }


def _box_area(box: dict) -> int:
    return max(0, box.get("width", 0)) * max(0, box.get("height", 0))


def iou(a: dict, b: dict) -> float:
    ax1, ay1 = a.get("x", 0), a.get("y", 0)
    ax2, ay2 = ax1 + a.get("width", 0), ay1 + a.get("height", 0)
    bx1, by1 = b.get("x", 0), b.get("y", 0)
    bx2, by2 = bx1 + b.get("width", 0), by1 + b.get("height", 0)
    inter_w = max(0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    union = _box_area(a) + _box_area(b) - inter
    return inter / union if union else 0.0


def _looks_like_formula(text: str) -> bool:
    return any(marker in text for marker in FORMULA_MARKERS) and bool(re.search(r"[A-Za-z0-9]", text))


def _text_to_latex(text: str) -> str:
    latex = text.strip()
    replacements = {
        "²": "^2",
        "³": "^3",
        "×": r"\times ",
        "÷": r"\div ",
        "≤": r"\le ",
        "≥": r"\ge ",
        "≠": r"\ne ",
        "≈": r"\approx ",
        "→": r"\to ",
        "∞": r"\infty ",
    }
    for source, target in replacements.items():
        latex = latex.replace(source, target)
    latex = re.sub(r"([A-Za-z0-9)\]])\^(\d+)", r"\1^{\2}", latex)
    for name in ("lim", "sin", "cos", "tan", "log", "ln"):
        latex = re.sub(fr"\b{name}\b", fr"\\{name}", latex)
    return latex


def _heuristic_formula_blocks(ocr_blocks: list[dict]) -> list[dict]:
    blocks = []
    for block in ocr_blocks or []:
        text = str(block.get("text", "")).strip()
        if not text or not _looks_like_formula(text):
            continue
        box = _bbox(block)
        blocks.append(
            {
                "latex": _text_to_latex(text),
                "text": text,
                "confidence": float(block.get("confidence", 0.72) or 0.72),
                "bbox": box,
                "box": box,
                "source": "heuristic",
            }
        )
    return blocks


def _layout_formula_regions(layout_context: dict | None) -> list[dict]:
    regions = []
    for item in (layout_context or {}).get("detections", []) or []:
        label = str(item.get("label", "")).lower()
        if label != "formula":
            continue
        box = _bbox(item)
        if box["width"] > 0 and box["height"] > 0:
            regions.append({**item, "bbox": box, "box": box})
    return regions


def _crop_region(image_path: str, region: dict, index: int) -> str:
    import cv2
    import numpy as np

    source = Path(image_path)
    data = np.fromfile(str(source), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return ""
    box = _bbox(region)
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]
    crop = image[max(0, y) : max(0, y + h), max(0, x) : max(0, x + w)]
    if crop.size == 0:
        return ""
    output_dir = source.parents[1] / "processed" / "formula"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{source.stem}_{index:02d}_formula.png"
    success, encoded = cv2.imencode(".png", crop)
    if not success:
        return ""
    encoded.tofile(str(output_path))
    return str(output_path)


def _extract_latex(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("latex", "text", "content", "formula"):
            if value.get(key):
                return str(value[key]).strip()
        for key in ("res", "results", "items"):
            nested = _extract_latex(value.get(key))
            if nested:
                return nested
    if isinstance(value, list):
        parts = [_extract_latex(item) for item in value]
        return " ".join(item for item in parts if item).strip()
    return ""


def _recognize_with_pix2text(image_path: str) -> str:
    engine = _get_pix2text()
    if engine is None:
        return ""
    for method_name in ("recognize_formula", "recognize", "__call__"):
        method = getattr(engine, method_name, None)
        if not callable(method):
            continue
        try:
            return _extract_latex(method(image_path))
        except Exception:
            continue
    return ""


def detect_formulas(
    image_path: str,
    *,
    ocr_blocks: list[dict],
    layout_context: dict | None = None,
    db: Session | None = None,
    task_id: int | None = None,
) -> list[dict]:
    start = perf_counter()
    provider = settings.formula_provider.lower().strip()
    formulas: list[dict] = []
    regions = _layout_formula_regions(layout_context)
    status = "success"
    error_message = ""

    try:
        if provider == "off":
            formulas = []
        elif provider == "pix2text":
            for index, region in enumerate(regions, start=1):
                crop_path = _crop_region(image_path, region, index)
                latex = _recognize_with_pix2text(crop_path) if crop_path else ""
                if not latex:
                    continue
                box = _bbox(region)
                formulas.append(
                    {
                        "latex": latex,
                        "text": latex,
                        "confidence": float(region.get("confidence", 0.82) or 0.82),
                        "bbox": box,
                        "box": box,
                        "source": "pix2text",
                        "cropUrl": path_to_upload_url(crop_path) if crop_path else "",
                    }
                )
            if not formulas and not regions:
                latex = _recognize_with_pix2text(image_path)
                if latex and _looks_like_formula(latex):
                    formulas.append(
                        {
                            "latex": latex,
                            "text": latex,
                            "confidence": 0.68,
                            "bbox": {"x": 0, "y": 0, "width": 0, "height": 0},
                            "box": {"x": 0, "y": 0, "width": 0, "height": 0},
                            "source": "pix2text-full-image",
                        }
                    )
            if not formulas:
                formulas = _heuristic_formula_blocks(ocr_blocks)
        else:
            formulas = _heuristic_formula_blocks(ocr_blocks)
    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        formulas = _heuristic_formula_blocks(ocr_blocks)

    cost = int((perf_counter() - start) * 1000)
    if db:
        create_model_log(
            db,
            task_id=task_id,
            model_type="formula",
            model_name=f"{provider or 'heuristic'}-formula",
            stage="formula_running",
            error_code="FORMULA_FAILED" if status == "failed" else "",
            input_summary=image_path,
            output_summary=f"识别公式块 {len(formulas)} 个",
            metadata={"regions": len(regions), "fallback": any(item.get("source") == "heuristic" for item in formulas)},
            status=status,
            cost_time=cost,
            error_message=error_message,
        )
    return formulas


def merge_text_and_formula_blocks(ocr_blocks: list[dict], formula_blocks: list[dict]) -> dict:
    merged = []
    formula_boxes = [_bbox(item) for item in formula_blocks or []]
    for block in ocr_blocks or []:
        box = _bbox(block)
        overlap = max((iou(box, formula_box) for formula_box in formula_boxes), default=0.0)
        item = {
            "type": "text",
            "text": str(block.get("text", "")).strip(),
            "confidence": float(block.get("confidence", 0) or 0),
            "bbox": box,
            "box": box,
            "overlappedByFormula": overlap > 0.35,
        }
        if item["text"]:
            merged.append(item)
    for block in formula_blocks or []:
        box = _bbox(block)
        latex = str(block.get("latex") or block.get("text") or "").strip()
        if latex:
            merged.append(
                {
                    "type": "formula",
                    "latex": latex,
                    "text": f"${latex}$",
                    "confidence": float(block.get("confidence", 0) or 0),
                    "bbox": box,
                    "box": box,
                    "source": block.get("source", "formula"),
                }
            )

    merged.sort(key=lambda item: (item["bbox"].get("y", 0), item["bbox"].get("x", 0)))
    readable = [item["text"] for item in merged if item.get("type") == "formula" or not item.get("overlappedByFormula")]
    return {"mergedBlocks": merged, "mergedText": "\n".join(part for part in readable if part).strip()}
