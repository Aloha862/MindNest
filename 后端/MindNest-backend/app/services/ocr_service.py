from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Any

from app.config import settings
from app.services.vision_model_client import call_vision_model, is_vision_model_configured


REAL_OCR_PROVIDERS = {"qwen", "dashscope", "aliyun", "tongyi", "vlm"}


@lru_cache
def _get_paddle_ocr():
    """Lazily initialize PaddleOCR.

    On some Windows + PaddlePaddle builds, oneDNN/MKLDNN can trigger runtime
    attribute conversion errors. Disabling it here keeps the course project
    usable on common student machines.
    """
    if not settings.paddleocr_enabled and settings.ocr_provider.lower() != "paddle":
        return None

    os.environ.setdefault("FLAGS_use_mkldnn", "0")
    os.environ.setdefault("FLAGS_enable_onednn", "0")
    os.environ.setdefault("PADDLE_DISABLE_MKLDNN", "1")

    try:
        from paddleocr import PaddleOCR

        try:
            return PaddleOCR(use_angle_cls=True, lang="ch", show_log=False, enable_mkldnn=False)
        except TypeError:
            return PaddleOCR(
                lang="ch",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
    except Exception:
        return None


def _mock_ocr() -> dict:
    return {
        "rawText": "1. 已知函数 f(x)=x^2+2x，求 f'(x)。\nA. 2x\nB. 2x+2\nC. x+2\nD. 2",
        "blocks": [
            {
                "text": "1. 已知函数 f(x)=x^2+2x，求 f'(x)。",
                "confidence": 0.96,
                "box": {"x": 10, "y": 20, "width": 420, "height": 40},
            },
            {"text": "A. 2x", "confidence": 0.94, "box": {"x": 20, "y": 80, "width": 120, "height": 32}},
            {"text": "B. 2x+2", "confidence": 0.95, "box": {"x": 20, "y": 120, "width": 140, "height": 32}},
            {"text": "C. x+2", "confidence": 0.93, "box": {"x": 20, "y": 160, "width": 120, "height": 32}},
            {"text": "D. 2", "confidence": 0.93, "box": {"x": 20, "y": 200, "width": 100, "height": 32}},
        ],
        "formulaBlocks": [
            {"latex": "f(x)=x^2+2x", "confidence": 0.92, "box": {"x": 92, "y": 20, "width": 140, "height": 32}},
            {"latex": "f'(x)=2x+2", "confidence": 0.9, "box": {"x": 48, "y": 120, "width": 120, "height": 32}},
        ],
    }


def _unconfigured_ocr(message: str) -> dict:
    return {
        "rawText": message,
        "blocks": [
            {
                "text": message,
                "confidence": 0,
                "box": {"x": 0, "y": 0, "width": 0, "height": 0},
            }
        ],
        "formulaBlocks": [],
        "warning": message,
    }


def _looks_like_formula(text: str) -> bool:
    markers = [
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
        "∞",
        "frac",
        "sin",
        "cos",
        "tan",
        "f(",
        "g(",
        "^",
        "²",
        "³",
    ]
    return any(marker in text for marker in markers) and bool(re.search(r"[A-Za-z0-9]", text))


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
    latex = re.sub(r"\blim\b", r"\\lim", latex)
    latex = re.sub(r"\bsin\b", r"\\sin", latex)
    latex = re.sub(r"\bcos\b", r"\\cos", latex)
    latex = re.sub(r"\btan\b", r"\\tan", latex)
    return latex


def _extract_latex_segments(text: str) -> list[str]:
    patterns = [
        r"\$\$(.+?)\$\$",
        r"\\\[(.+?)\\\]",
        r"\\\((.+?)\\\)",
        r"\$(.+?)\$",
    ]
    values: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.S):
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if value and value not in values:
                values.append(value)
    return values


def _box_from_points(points: Any) -> dict:
    try:
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        return {
            "x": int(min(xs)),
            "y": int(min(ys)),
            "width": int(max(xs) - min(xs)),
            "height": int(max(ys) - min(ys)),
        }
    except Exception:
        return {"x": 0, "y": 0, "width": 0, "height": 0}


def _box_from_flat_box(box: Any) -> dict:
    try:
        values = [float(item) for item in box]
        if len(values) >= 4:
            x1, y1, x2, y2 = values[:4]
            return {"x": int(x1), "y": int(y1), "width": int(x2 - x1), "height": int(y2 - y1)}
    except Exception:
        pass
    return {"x": 0, "y": 0, "width": 0, "height": 0}


def _infer_formula_blocks(blocks: list[dict]) -> list[dict]:
    formula_blocks = []
    for block in blocks:
        text = str(block.get("text", "")).strip()
        if not text or not _looks_like_formula(text):
            continue
        segments = _extract_latex_segments(text) or [text]
        for segment in segments:
            formula_blocks.append(
                {
                    "latex": _text_to_latex(segment),
                    "text": segment,
                    "confidence": float(block.get("confidence", 0.75) or 0.75),
                    "box": block.get("box", {"x": 0, "y": 0, "width": 0, "height": 0}),
                    "source": "heuristic",
                }
            )
    return formula_blocks


def _box_from_tongyi_pos(pos_list: Any) -> dict:
    if not isinstance(pos_list, list) or not pos_list:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    first = pos_list[0] or {}
    rotate_rect = first.get("rotate_rect") if isinstance(first, dict) else None
    if isinstance(rotate_rect, list) and len(rotate_rect) >= 4:
        try:
            cx, cy, width, height = [float(item) for item in rotate_rect[:4]]
            return {
                "x": max(0, int(cx - width / 2)),
                "y": max(0, int(cy - height / 2)),
                "width": max(0, int(width)),
                "height": max(0, int(height)),
            }
        except Exception:
            pass
    return {"x": 0, "y": 0, "width": 0, "height": 0}


def _pick_text_from_dict(value: dict) -> str:
    for key in ("rawText", "raw_text", "rawTex", "raw_tex", "question", "answer", "text", "content", "latex"):
        if value.get(key):
            return str(value.get(key))
    return ""


def _normalize_ocr_text(text: Any) -> str:
    value = str(text or "")
    # Some VLM OCR responses contain literal "\n" inside JSON strings after
    # tolerant LaTeX escaping. Restore only line-break-looking markers, while
    # leaving LaTeX commands such as \neq or \nabla untouched.
    value = re.sub(r"\\n(?=\\n|\$|[\u4e00-\u9fff]|[（(]|$)", "\n", value)
    return value.strip()


def _normalize_any_block(item: Any, default_source: str = "tongyi") -> dict | None:
    if isinstance(item, str):
        text = _normalize_ocr_text(item)
        if not text:
            return None
        return {
            "text": text,
            "confidence": 0.9,
            "box": {"x": 0, "y": 0, "width": 0, "height": 0},
            "source": default_source,
        }
    if isinstance(item, list):
        text = _normalize_ocr_text(" ".join(str(part).strip() for part in item if str(part).strip()))
        if not text:
            return None
        return {
            "text": text,
            "confidence": 0.9,
            "box": {"x": 0, "y": 0, "width": 0, "height": 0},
            "source": default_source,
        }
    if not isinstance(item, dict):
        return None
    text = _normalize_ocr_text(_pick_text_from_dict(item))
    if not text:
        return None
    return {
        "text": text,
        "confidence": float(item.get("confidence", item.get("score", 0.9)) or 0.9),
        "box": item.get("box") or item.get("bbox") or _box_from_tongyi_pos(item.get("pos_list")),
        "source": item.get("source") or default_source,
    }


def _normalize_any_formula(item: Any, default_source: str = "tongyi") -> dict | None:
    block = _normalize_any_block(item, default_source)
    if not block:
        return None
    text = block["text"]
    segments = _extract_latex_segments(text) or [text]
    latex = _text_to_latex(segments[0])
    return {
        "latex": latex,
        "text": segments[0],
        "confidence": block["confidence"],
        "box": block["box"],
        "source": block["source"],
    }


def _normalize_vlm_ocr_result(result: Any) -> dict:
    if isinstance(result, list):
        normalized_blocks = [_normalize_any_block(item) for item in result]
        blocks = [item for item in normalized_blocks if item]
        raw_text = "\n".join(item["text"] for item in blocks)
        return {"rawText": raw_text, "blocks": blocks, "formulaBlocks": _infer_formula_blocks(blocks)}
    if not isinstance(result, dict):
        raw_text = str(result or "")
        blocks = [_normalize_any_block(raw_text)] if raw_text else []
        return {"rawText": raw_text, "blocks": [item for item in blocks if item], "formulaBlocks": []}

    raw_text = (
        result.get("rawText")
        or result.get("raw_text")
        or result.get("rawTex")
        or result.get("raw_tex")
        or result.get("question")
        or result.get("answer")
        or result.get("text")
        or result.get("content")
        or ""
    )
    raw_text = _normalize_ocr_text(raw_text)
    blocks = result.get("blocks") or []
    if not blocks and isinstance(result.get("items"), list):
        blocks = result.get("items")
    if not blocks and isinstance(result.get("lines"), list):
        blocks = result.get("lines")
    formula_blocks = result.get("formulaBlocks") or result.get("formula_blocks") or []
    if not isinstance(blocks, list):
        blocks = [blocks]
    blocks = [item for item in (_normalize_any_block(item) for item in blocks) if item]
    if not isinstance(formula_blocks, list):
        formula_blocks = [formula_blocks]
    formula_blocks = [item for item in (_normalize_any_formula(item) for item in formula_blocks) if item]
    if raw_text and not blocks:
        blocks = [
            {
                "text": str(raw_text),
                "confidence": float(result.get("confidence", 0.9) or 0.9),
                "box": _box_from_tongyi_pos(result.get("pos_list")),
                "source": "tongyi",
            }
        ]
    if not formula_blocks:
        formula_blocks = _infer_formula_blocks(blocks)
    return {"rawText": raw_text, "blocks": blocks, "formulaBlocks": formula_blocks}


def _run_vlm_ocr(image_path: str) -> dict:
    prompt = """
你是智学空间(MindNest)的 OCR 与公式识别模型。请准确识别图片中的中文、英文、数字、题号、选项、解析文字和数学公式。

要求：
1. 只返回 JSON，不要返回 Markdown。
2. rawText 按图片阅读顺序输出完整文字。
3. blocks 按阅读顺序输出文本块；如果无法确定位置，box 填 0。
4. formulaBlocks 输出图片中的数学公式，latex 字段尽量使用 LaTeX；没有公式返回空数组。
5. 不要使用示例题目，不要编造图片中不存在的内容。

返回格式：
{
  "rawText": "完整识别文字",
  "blocks": [
    {
      "text": "文本块",
      "confidence": 0.9,
      "box": {"x": 0, "y": 0, "width": 0, "height": 0}
    }
  ],
  "formulaBlocks": [
    {
      "latex": "公式 LaTeX",
      "confidence": 0.8,
      "box": {"x": 0, "y": 0, "width": 0, "height": 0}
    }
  ]
}
"""
    prompt = """
你是智学空间(MindNest)的高精度 OCR 模型。请准确识别图片中的中文、英文、数字、题号、选项、解析文字和数学公式。
要求：
1. 只返回 JSON 对象，不要返回 Markdown、解释文字或代码块。
2. rawText 按图片阅读顺序输出完整文字，保留题号、选项和必要换行。
3. blocks 按阅读顺序输出文本块；如果无法确定位置，box 填 0。
4. formulaBlocks 输出图片中的数学公式，latex 字段使用标准 LaTeX；没有公式返回空数组。
5. 不要使用示例题目，不要编造图片中不存在的内容。
返回格式：
{
  "rawText": "完整识别文字",
  "blocks": [
    {
      "text": "文本块",
      "confidence": 0.9,
      "box": {"x": 0, "y": 0, "width": 0, "height": 0}
    }
  ],
  "formulaBlocks": [
    {
      "latex": "公式 LaTeX",
      "confidence": 0.8,
      "box": {"x": 0, "y": 0, "width": 0, "height": 0}
    }
  ]
}
"""
    prompt = """
你是智学空间(MindNest)的 OCR 文本识别模型。请只做图片文字转写，不要做题目解析，不要重写答案，不要把公式重新排版成单独的公式块。

要求：
1. 只返回 JSON 对象，不要返回 Markdown、解释文字或代码块。
2. rawText 按图片从上到下、从左到右的阅读顺序输出完整文本。
3. 保留必要换行，例如题干、分析、证明、公式、方法总结应各自成行。
4. 数学公式必须保留在 rawText 的原始上下文位置，并尽量改写为标准 LaTeX，用 $...$ 包裹，例如“当 $x \\to 0$ 时，$\\ln(x+\\sqrt{1+x^2}) \\sim x$”。
5. 不要把公式放入 formulaBlocks，不要输出独立公式区域；formulaBlocks 固定返回空数组。
6. blocks 按阅读顺序输出文本块；如果无法确定位置，box 填 0。
7. 不要使用示例题目，不要编造图片中不存在的内容。

返回格式：
{
  "rawText": "完整识别文字",
  "blocks": [
    {
      "text": "文本块",
      "confidence": 0.9,
      "box": {"x": 0, "y": 0, "width": 0, "height": 0}
    }
  ],
  "formulaBlocks": []
}
"""
    prompt = """
你是智学空间(MindNest)的高精度 OCR 转写模型。请只做图片文字转写，不要解题，不要补写，不要改写答案。

识别规则：
1. 只返回 JSON 对象，不要返回 Markdown、解释文本或代码块。
2. rawText 以黑色印刷正文为主，按图片从上到下、从左到右的阅读顺序完整输出。
3. 蓝色手写批注、箭头旁注、圈画说明不要插入 rawText 正文；如果批注会打断主文阅读，直接忽略。
4. 数学公式必须保留在 rawText 的原始上下文位置，并尽量写成标准 LaTeX，用 $...$ 包裹。
5. 保留必要换行：题干、选项、解答段、关键公式、结论尽量分行；不要把整页压成一行。
6. 不要把公式放入 formulaBlocks，不要输出独立公式区域；formulaBlocks 固定返回空数组。
7. 不要使用示例题目，不要编造图片中不存在的内容。

返回格式：
{
  "rawText": "完整识别文字",
  "blocks": [
    {
      "text": "文本块",
      "confidence": 0.9,
      "box": {"x": 0, "y": 0, "width": 0, "height": 0}
    }
  ],
  "formulaBlocks": []
}
"""
    result = _normalize_vlm_ocr_result(
        call_vision_model(
            image_path,
            prompt,
            timeout=60,
            model_name=settings.ocr_model_name,
            include_thinking=False,
            fallback_text_field="rawText",
        )
    )
    result["formulaBlocks"] = []
    return result


def _call_paddle(ocr, image_path: str):
    try:
        return ocr.ocr(image_path, cls=True)
    except TypeError as exc:
        if "cls" not in str(exc):
            raise
    try:
        return ocr.ocr(image_path)
    except NotImplementedError:
        raise
    except Exception:
        if hasattr(ocr, "predict"):
            return ocr.predict(image_path)
        raise


def _as_dict(item: Any) -> dict | None:
    if isinstance(item, dict):
        return item
    for method_name in ("to_dict", "json"):
        method = getattr(item, method_name, None)
        if not callable(method):
            continue
        try:
            value = method()
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                import json

                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else None
        except Exception:
            continue
    return None


def _blocks_to_reading_text(blocks: list[dict]) -> str:
    """Merge OCR boxes into visual reading lines.

    PaddleOCR often splits formulas into several small boxes. Joining every box
    with a newline makes one printed line appear as multiple vertical lines in
    the UI. This groups boxes with close vertical centers and orders them left
    to right, which is closer to the page layout while still keeping OCR output
    as plain text.
    """
    if not blocks:
        return ""

    def box_value(block: dict, key: str) -> float:
        try:
            return float((block.get("box") or {}).get(key, 0) or 0)
        except Exception:
            return 0.0

    valid_blocks = [block for block in blocks if str(block.get("text", "")).strip()]
    heights = [box_value(block, "height") for block in valid_blocks if box_value(block, "height") > 0]
    median_height = sorted(heights)[len(heights) // 2] if heights else 18
    y_threshold = max(10.0, median_height * 0.8)

    rows: list[dict] = []
    for block in sorted(valid_blocks, key=lambda item: (box_value(item, "y") + box_value(item, "height") / 2, box_value(item, "x"))):
        y = box_value(block, "y")
        h = box_value(block, "height") or median_height
        center = y + h / 2
        target = None
        best_distance = None
        for row in rows:
            distance = abs(center - row["center"])
            if distance <= max(y_threshold, row["height"] * 0.65):
                if best_distance is None or distance < best_distance:
                    target = row
                    best_distance = distance
        if target is None:
            rows.append({"center": center, "height": h, "items": [block]})
        else:
            target["items"].append(block)
            count = len(target["items"])
            target["center"] = (target["center"] * (count - 1) + center) / count
            target["height"] = max(target["height"], h)

    lines: list[str] = []
    for row in sorted(rows, key=lambda item: item["center"]):
        parts: list[str] = []
        previous_right = None
        for block in sorted(row["items"], key=lambda item: box_value(item, "x")):
            text = str(block.get("text", "")).strip()
            if not text:
                continue
            x = box_value(block, "x")
            width = box_value(block, "width")
            if parts and previous_right is not None and x - previous_right > max(8.0, row["height"] * 0.35):
                parts.append(" ")
            parts.append(text)
            previous_right = max(previous_right or 0, x + width)
        line = "".join(parts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _parse_paddle_result(result: Any) -> dict:
    blocks: list[dict] = []
    texts: list[str] = []

    def add_block(text: Any, confidence: Any = 0.8, box: Any = None) -> None:
        content = str(text or "").strip()
        if not content:
            return
        try:
            score = float(confidence)
        except Exception:
            score = 0.8
        block = {
            "text": content,
            "confidence": score,
            "box": box if isinstance(box, dict) else {"x": 0, "y": 0, "width": 0, "height": 0},
        }
        texts.append(content)
        blocks.append(block)

    def parse_old_line(line: Any) -> bool:
        if not isinstance(line, (list, tuple)) or len(line) < 2:
            return False
        box_points, text_info = line[0], line[1]
        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
            add_block(text_info[0], text_info[1], _box_from_points(box_points))
            return True
        return False

    def parse_dict(item: dict) -> bool:
        rec_texts = item.get("rec_texts") or item.get("texts") or item.get("text")
        rec_scores = item.get("rec_scores") or item.get("scores") or item.get("confidence")
        rec_boxes = item.get("rec_boxes") or item.get("dt_polys") or item.get("rec_polys") or item.get("boxes")
        if isinstance(rec_texts, str):
            add_block(rec_texts, rec_scores or 0.8, _box_from_flat_box(rec_boxes) if rec_boxes else None)
            return True
        if not isinstance(rec_texts, list):
            return False
        for index, text in enumerate(rec_texts):
            score = rec_scores[index] if isinstance(rec_scores, list) and index < len(rec_scores) else 0.8
            raw_box = rec_boxes[index] if isinstance(rec_boxes, list) and index < len(rec_boxes) else None
            if raw_box and isinstance(raw_box, (list, tuple)) and raw_box and isinstance(raw_box[0], (list, tuple)):
                box = _box_from_points(raw_box)
            else:
                box = _box_from_flat_box(raw_box) if raw_box else None
            add_block(text, score, box)
        return True

    candidates = result if isinstance(result, list) else [result]
    for item in candidates:
        item_dict = _as_dict(item)
        if item_dict and parse_dict(item_dict):
            continue
        if isinstance(item, list):
            if item and all(parse_old_line(line) for line in item if line):
                continue
            for sub_item in item:
                sub_dict = _as_dict(sub_item)
                if sub_dict:
                    parse_dict(sub_dict)
                else:
                    parse_old_line(sub_item)
        else:
            parse_old_line(item)

    return {"rawText": _blocks_to_reading_text(blocks) or "\n".join(texts), "blocks": blocks, "formulaBlocks": _infer_formula_blocks(blocks)}


def get_ocr_model_name() -> str:
    provider = settings.ocr_provider.lower().strip()
    if provider in REAL_OCR_PROVIDERS and is_vision_model_configured(provider=provider, model_name=settings.ocr_model_name):
        return f"{provider}:{settings.ocr_model_name}:ocr"
    if settings.paddleocr_enabled or provider == "paddle":
        return "paddleocr"
    return "mock-ocr-v1"


def run_ocr(image_path: str) -> dict:
    provider = settings.ocr_provider.lower().strip()
    if provider in REAL_OCR_PROVIDERS and is_vision_model_configured(provider=provider, model_name=settings.ocr_model_name):
        return _run_vlm_ocr(image_path)

    ocr = _get_paddle_ocr()
    if not ocr:
        if provider in REAL_OCR_PROVIDERS | {"paddle"}:
            return _unconfigured_ocr(
                "真实 OCR 未生效：请检查 DASHSCOPE_API_KEY/VLM_API_KEY，或安装并启用 PaddleOCR。当前没有使用固定 mock 题目。"
            )
        return _mock_ocr()

    try:
        result = _call_paddle(ocr, image_path)
        parsed = _parse_paddle_result(result)
        if not parsed["rawText"]:
            return _unconfigured_ocr("PaddleOCR 已调用，但没有识别到有效文字。请检查图片清晰度或 PaddleOCR 安装。")
        return parsed
    except Exception as exc:
        if provider in REAL_OCR_PROVIDERS | {"paddle"}:
            return _unconfigured_ocr(f"PaddleOCR 调用失败：{exc}")
        return _mock_ocr()
