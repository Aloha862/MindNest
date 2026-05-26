# -*- coding: utf-8 -*-
"""Build the SnapMatch 5-class YOLO layout dataset.

The script creates a reproducible research dataset by combining:
- remapped labels from the original 9-class local dataset
- synthetic university question pages with phone-photo distortions

Class order:
0 question
1 diagram
2 formula
3 answer
4 analysis
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


CLASS_NAMES = ["question", "diagram", "formula", "answer", "analysis"]
OLD_TO_NEW = {
    3: 2,  # formula
    4: 4,  # analysis
    5: 3,  # answer
    6: 1,  # diagram
    7: 1,  # table -> diagram
}
OLD_QUESTION_CLASSES = {0, 1, 2}
OLD_QUESTION_CONTENT_CLASSES = {1, 2, 3, 6, 7}
OLD_SECTION_BREAK_CLASSES = {4, 5}
IGNORED_OLD_CLASSES = {8}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass(frozen=True)
class Box:
    cls: int
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    def clipped(self, width: int, height: int) -> "Box":
        return Box(
            self.cls,
            min(max(self.x1, 0), width),
            min(max(self.y1, 0), height),
            min(max(self.x2, 0), width),
            min(max(self.y2, 0), height),
        )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def font_path(name: str = "msyh.ttc") -> str:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return ""


FONT_REGULAR = font_path("msyh.ttc")
FONT_BOLD = font_path("msyhbd.ttc")
FONT_MONO = font_path("consola.ttf")


def load_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = FONT_MONO if mono and FONT_MONO else FONT_BOLD if bold and FONT_BOLD else FONT_REGULAR
    if path:
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def safe_reset_dir(path: Path) -> None:
    resolved = path.resolve()
    root = repo_root().resolve()
    if root not in resolved.parents:
        raise RuntimeError(f"Refusing to reset path outside repo: {resolved}")
    if not resolved.name.endswith("v2_5class"):
        raise RuntimeError(f"Refusing to reset unexpected output directory: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def yolo_to_box(cls_id: int, x: float, y: float, w: float, h: float, width: int, height: int) -> Box:
    cx = x * width
    cy = y * height
    bw = w * width
    bh = h * height
    return Box(cls_id, cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2).clipped(width, height)


def box_to_yolo(box: Box, width: int, height: int) -> str:
    x1, y1, x2, y2 = box.clipped(width, height).x1, box.clipped(width, height).y1, box.clipped(width, height).x2, box.clipped(width, height).y2
    cx = ((x1 + x2) / 2) / width
    cy = ((y1 + y2) / 2) / height
    bw = (x2 - x1) / width
    bh = (y2 - y1) / height
    return f"{box.cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"


def union_box(cls_id: int, boxes: list[Box]) -> Box:
    return Box(
        cls_id,
        min(box.x1 for box in boxes),
        min(box.y1 for box in boxes),
        max(box.x2 for box in boxes),
        max(box.y2 for box in boxes),
    )


def read_image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def read_old_labels(path: Path, width: int, height: int) -> list[Box]:
    if not path.exists():
        return []
    boxes: list[Box] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        cls_id = int(float(parts[0]))
        x, y, w, h = [float(item) for item in parts[1:]]
        boxes.append(yolo_to_box(cls_id, x, y, w, h, width, height))
    return boxes


def dedupe_boxes(boxes: list[Box], iou_threshold: float = 0.92) -> list[Box]:
    kept: list[Box] = []
    for box in sorted(boxes, key=lambda item: item.area, reverse=True):
        duplicate = False
        for existing in kept:
            if box.cls == existing.cls and iou(box, existing) >= iou_threshold:
                duplicate = True
                break
        if not duplicate and box.area > 16:
            kept.append(box)
    return sorted(kept, key=lambda item: (item.y1, item.x1, item.cls))


def iou(a: Box, b: Box) -> float:
    x1 = max(a.x1, b.x1)
    y1 = max(a.y1, b.y1)
    x2 = min(a.x2, b.x2)
    y2 = min(a.y2, b.y2)
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = a.area + b.area - inter
    return inter / union if union else 0.0


def remap_existing_labels(old_boxes: list[Box], width: int, height: int) -> list[Box]:
    result: list[Box] = []
    old_question = [box for box in old_boxes if box.cls in OLD_QUESTION_CLASSES]
    question_content = [box for box in old_boxes if box.cls in OLD_QUESTION_CONTENT_CLASSES]
    section_breaks = [box for box in old_boxes if box.cls in OLD_SECTION_BREAK_CLASSES]
    anchors = [box for box in old_boxes if box.cls == 0]
    if anchors:
        for anchor in anchors:
            cutoff = anchor.y2
            for breaker in section_breaks:
                center_y = (breaker.y1 + breaker.y2) / 2
                if anchor.y1 <= center_y <= anchor.y2:
                    cutoff = min(cutoff, breaker.y1)
            related = []
            for box in question_content:
                center_y = (box.y1 + box.y2) / 2
                if anchor.y1 - height * 0.03 <= center_y <= cutoff + height * 0.02:
                    related.append(box)
            if related:
                merged = union_box(0, related)
                pad_x = max(8, width * 0.015)
                pad_y = max(6, height * 0.01)
                result.append(
                    Box(
                        0,
                        max(anchor.x1, merged.x1 - pad_x),
                        max(anchor.y1, merged.y1 - pad_y),
                        min(anchor.x2, merged.x2 + pad_x),
                        min(cutoff, merged.y2 + pad_y),
                    ).clipped(width, height)
                )
            elif cutoff > anchor.y1 + height * 0.05:
                result.append(Box(0, anchor.x1, anchor.y1, anchor.x2, cutoff).clipped(width, height))
    elif old_question:
        candidates = question_content or old_question
        result.append(union_box(0, candidates).clipped(width, height))

    for box in old_boxes:
        if box.cls in OLD_TO_NEW:
            result.append(Box(OLD_TO_NEW[box.cls], box.x1, box.y1, box.x2, box.y2).clipped(width, height))
        elif box.cls in IGNORED_OLD_CLASSES or box.cls in OLD_QUESTION_CLASSES:
            continue
    return dedupe_boxes(result)


def write_labels(path: Path, boxes: list[Box], width: int, height: int) -> None:
    lines = []
    for box in boxes:
        clipped = box.clipped(width, height)
        if clipped.width <= 2 or clipped.height <= 2:
            continue
        lines.append(box_to_yolo(clipped, width, height))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw_line in text.split("\n"):
        current = ""
        for char in raw_line:
            trial = current + char
            if current and text_width(draw, trial, font) > max_width:
                lines.append(current)
                current = char
            else:
                current = trial
        if current:
            lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    max_width: int,
    line_gap: int = 6,
) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y = bbox[3] + line_gap
    return y


def rand_subject(rng: random.Random) -> str:
    return rng.choice(["高等数学", "大学英语", "马克思主义基本原理", "计算机组成原理", "数据结构", "操作系统"])


def subject_question(subject: str, rng: random.Random) -> tuple[str, str, str]:
    number = rng.randint(1, 36)
    if subject == "高等数学":
        q = rng.choice(
            [
                f"{number}. 设函数 f(x)=x^3-3x+a，讨论 f(x) 在区间 [-2,2] 上的单调性，并求极值。",
                f"{number}. 计算定积分 ∫_0^1 (x^2+2x+1) dx，并说明几何意义。",
                f"{number}. 求微分方程 y' + 2y = e^(-x) 的通解。",
                f"{number}. 设 A 为三阶矩阵，已知特征值为 1,2,3，求 det(A^2-2A+I)。",
            ]
        )
        answer = rng.choice(["答案：极大值为 2+a，极小值为 -2+a。", "答案：积分值为 7/3。", "答案：y = Ce^(-2x)+e^(-x)。"])
        analysis = "解析：先确定定义域与关键点，再利用导数、矩阵特征值或积分性质化简。注意端点值也需要纳入比较。"
    elif subject == "大学英语":
        q = rng.choice(
            [
                f"{number}. Read the passage and choose the best answer. The author mainly argues that technology changes learning habits.",
                f"{number}. Translate the underlined sentence into Chinese and summarize the main idea of the paragraph.",
                f"{number}. Choose the word that best completes the sentence: The policy is expected to ______ innovation in universities.",
            ]
        )
        answer = rng.choice(["答案：B", "答案：该句强调技术改变学习方式。", "答案：promote"])
        analysis = "解析：根据主题句、转折词和上下文指代关系判断，选项中应排除与原文程度不一致的表述。"
    elif subject == "马克思主义基本原理":
        q = rng.choice(
            [
                f"{number}. 结合社会存在与社会意识的关系，说明实践在认识发展中的作用。",
                f"{number}. 简述矛盾普遍性和特殊性的辩证关系，并举例说明。",
                f"{number}. 说明人民群众是历史创造者的基本依据。",
            ]
        )
        answer = "答案：应从实践基础、辩证关系、历史主体三个层面作答。"
        analysis = "解析：答题时先给出原理，再结合材料展开，最后回到题目设问形成结论。"
    else:
        q = rng.choice(
            [
                f"{number}. 给定二叉树的先序和中序序列，写出后序遍历结果，并说明递归构造过程。",
                f"{number}. 分析下列程序片段的时间复杂度，并给出优化思路。",
                f"{number}. 画出流水线处理器在发生数据相关时的暂停周期，并说明转发机制。",
                f"{number}. 简述进程调度算法 RR 与 SJF 的区别，并分析适用场景。",
            ]
        )
        answer = rng.choice(["答案：后序遍历为 D E B F C A。", "答案：时间复杂度为 O(n log n)。", "答案：需要插入 1 个暂停周期。"])
        analysis = "解析：根据数据结构或系统机制逐步推导，先列出状态变化，再说明边界条件和复杂度。"
    return q, answer, analysis


def formula_text(rng: random.Random) -> str:
    return rng.choice(
        [
            "lim_{x→0} sin x / x = 1",
            "∫_0^1 (x^2 + 2x + 1) dx = 7/3",
            "A(n)=2A(n/2)+n,  A(n)=O(n log n)",
            "P(A|B)=P(AB)/P(B)",
            "f'(x)=3x^2-3,  x=±1",
            "T(n)=T(n-1)+n,  T(n)=O(n^2)",
        ]
    )


def draw_formula(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rng: random.Random) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=6, fill=(250, 250, 246), outline=(214, 214, 204), width=1)
    font = load_font(rng.randint(24, 32), mono=True)
    draw_wrapped(draw, (x1 + 16, y1 + 12), formula_text(rng), font, (30, 30, 30), x2 - x1 - 32, 8)


def draw_diagram(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rng: random.Random) -> None:
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill=(252, 252, 250), outline=(180, 185, 190), width=2)
    kind = rng.choice(["axis", "table", "flow", "bars"])
    if kind == "axis":
        ox, oy = x1 + 35, y2 - 30
        draw.line((ox, oy, x2 - 20, oy), fill=(70, 75, 80), width=2)
        draw.line((ox, oy, ox, y1 + 20), fill=(70, 75, 80), width=2)
        points = []
        for i in range(7):
            px = ox + i * max(1, (x2 - ox - 40) // 6)
            py = int(oy - (math.sin(i / 1.4) + 1.3) * (y2 - y1) / 4)
            points.append((px, py))
        draw.line(points, fill=(38, 101, 180), width=3)
    elif kind == "table":
        rows, cols = 4, 4
        for r in range(rows + 1):
            y = y1 + r * (y2 - y1) // rows
            draw.line((x1, y, x2, y), fill=(120, 125, 130), width=1)
        for c in range(cols + 1):
            x = x1 + c * (x2 - x1) // cols
            draw.line((x, y1, x, y2), fill=(120, 125, 130), width=1)
        font = load_font(18)
        for r in range(rows):
            for c in range(cols):
                draw.text((x1 + c * (x2 - x1) // cols + 10, y1 + r * (y2 - y1) // rows + 8), rng.choice(["A", "B", "1", "0", "n"]), font=font, fill=(60, 60, 60))
    elif kind == "flow":
        font = load_font(18)
        nodes = [
            (x1 + 20, y1 + 20, x1 + 130, y1 + 70, "输入"),
            (x1 + 170, y1 + 20, x1 + 300, y1 + 70, "处理"),
            (x1 + 90, y1 + 105, x1 + 230, y1 + 155, "输出"),
        ]
        for nx1, ny1, nx2, ny2, label in nodes:
            draw.rounded_rectangle((nx1, ny1, nx2, ny2), radius=8, outline=(85, 100, 115), width=2, fill=(245, 248, 252))
            draw.text((nx1 + 22, ny1 + 12), label, font=font, fill=(40, 45, 55))
        draw.line((x1 + 130, y1 + 45, x1 + 170, y1 + 45), fill=(85, 100, 115), width=2)
        draw.line((x1 + 235, y1 + 70, x1 + 170, y1 + 105), fill=(85, 100, 115), width=2)
    else:
        baseline = y2 - 24
        bar_w = max(16, (x2 - x1 - 70) // 6)
        for i in range(5):
            h = rng.randint(30, max(45, y2 - y1 - 40))
            bx1 = x1 + 35 + i * (bar_w + 16)
            draw.rectangle((bx1, baseline - h, bx1 + bar_w, baseline), fill=(70, 125, 176))
        draw.line((x1 + 24, baseline, x2 - 20, baseline), fill=(70, 70, 70), width=2)


def draw_hand_marks(draw: ImageDraw.ImageDraw, width: int, height: int, rng: random.Random) -> None:
    color = rng.choice([(210, 35, 35), (30, 85, 185), (210, 80, 45)])
    for _ in range(rng.randint(1, 4)):
        x = rng.randint(width // 5, width - width // 5)
        y = rng.randint(height // 5, height - height // 7)
        if rng.random() < 0.5:
            draw.arc((x - 25, y - 18, x + 42, y + 32), 15, 315, fill=color, width=3)
        else:
            draw.line((x, y + 20, x + 18, y + 38, x + 55, y - 10), fill=color, width=4)


def render_synthetic_page(split: str, index: int, rng: random.Random) -> tuple[Image.Image, list[Box]]:
    width = rng.randint(960, 1160)
    height = rng.randint(1450, 1760)
    page = Image.new("RGB", (width, height), rng.choice([(255, 255, 252), (252, 252, 248), (250, 251, 248)]))
    draw = ImageDraw.Draw(page)
    margin = rng.randint(64, 92)
    font_body = load_font(rng.randint(24, 29))
    font_title = load_font(rng.randint(27, 34), bold=True)
    font_small = load_font(rng.randint(21, 24))

    subject = rand_subject(rng)
    question, answer, analysis = subject_question(subject, rng)
    y = rng.randint(58, 92)
    draw.text((margin, y), f"{subject}  综合练习", font=font_small, fill=(80, 80, 80))
    y += rng.randint(44, 58)

    q_top = y
    q_text = question
    if "Choose" in question or "Read" in question:
        q_text += "\nA. increase cost   B. promote innovation   C. reduce demand   D. ignore evidence"
    elif rng.random() < 0.45:
        q_text += "\nA. 充分条件  B. 必要条件  C. 充要条件  D. 无法判断"
    y = draw_wrapped(draw, (margin, y), q_text, font_title, (25, 25, 25), width - margin * 2, 10)

    labels: list[Box] = []
    internal_bottom = y
    if rng.random() < 0.72:
        fw = rng.randint(int(width * 0.42), int(width * 0.72))
        fh = rng.randint(62, 105)
        fx1 = margin + rng.randint(0, max(1, width - margin * 2 - fw))
        fy1 = y + rng.randint(14, 34)
        draw_formula(draw, (fx1, fy1, fx1 + fw, fy1 + fh), rng)
        labels.append(Box(2, fx1, fy1, fx1 + fw, fy1 + fh))
        internal_bottom = max(internal_bottom, fy1 + fh)
        y = internal_bottom + rng.randint(18, 34)

    if rng.random() < 0.68:
        dw = rng.randint(int(width * 0.38), int(width * 0.70))
        dh = rng.randint(130, 230)
        dx1 = margin + rng.randint(0, max(1, width - margin * 2 - dw))
        dy1 = y + rng.randint(6, 24)
        draw_diagram(draw, (dx1, dy1, dx1 + dw, dy1 + dh), rng)
        labels.append(Box(1, dx1, dy1, dx1 + dw, dy1 + dh))
        internal_bottom = max(internal_bottom, dy1 + dh)
        y = internal_bottom + rng.randint(28, 46)

    prompt_tail = rng.choice(
        [
            "请写出主要步骤，并给出必要的说明。",
            "要求结合材料进行分析，结论必须明确。",
            "若存在多种方法，选择一种并说明理由。",
            "请根据图表或公式完成推导。",
        ]
    )
    y = draw_wrapped(draw, (margin, y), prompt_tail, font_body, (35, 35, 35), width - margin * 2, 8)
    q_bottom = min(height - 430, y + rng.randint(18, 42))
    labels.insert(0, Box(0, margin - 12, q_top - 12, width - margin + 12, q_bottom))

    y = q_bottom + rng.randint(32, 50)
    answer_top = y
    y = draw_wrapped(draw, (margin, y), answer, font_title, (24, 24, 24), width - margin * 2, 8)
    answer_bottom = y + rng.randint(16, 34)
    labels.append(Box(3, margin - 10, answer_top - 10, width - margin + 10, answer_bottom))

    y = answer_bottom + rng.randint(28, 48)
    analysis_top = y
    analysis_text = analysis
    if rng.random() < 0.55:
        analysis_text += "\n第一步：整理题干信息；第二步：建立模型或列式；第三步：验证结果是否符合题意。"
    y = draw_wrapped(draw, (margin, y), analysis_text, font_body, (34, 34, 34), width - margin * 2, 8)
    if rng.random() < 0.45:
        fw = rng.randint(int(width * 0.40), int(width * 0.65))
        fh = rng.randint(60, 96)
        fx1 = margin + rng.randint(0, max(1, width - margin * 2 - fw))
        fy1 = y + rng.randint(10, 24)
        draw_formula(draw, (fx1, fy1, fx1 + fw, fy1 + fh), rng)
        labels.append(Box(2, fx1, fy1, fx1 + fw, fy1 + fh))
        y = fy1 + fh + rng.randint(14, 26)
    analysis_bottom = min(height - 62, max(y + rng.randint(12, 30), analysis_top + 100))
    labels.append(Box(4, margin - 10, analysis_top - 10, width - margin + 10, analysis_bottom))

    for _ in range(rng.randint(8, 18)):
        x = rng.randint(margin // 2, width - margin // 2)
        yy = rng.randint(40, height - 50)
        shade = rng.randint(226, 238)
        draw.point((x, yy), fill=(shade, shade, shade))
    if rng.random() < 0.62:
        draw_hand_marks(draw, width, height, rng)

    page = page.filter(ImageFilter.GaussianBlur(radius=rng.choice([0, 0, 0.25, 0.45])))
    return apply_phone_effect(page, labels, rng)


def apply_phone_effect(page: Image.Image, labels: list[Box], rng: random.Random) -> tuple[Image.Image, list[Box]]:
    src_w, src_h = page.size
    bg_w = int(src_w * rng.uniform(1.12, 1.28))
    bg_h = int(src_h * rng.uniform(1.10, 1.24))
    bg_color = rng.choice([(218, 218, 214), (205, 207, 208), (230, 228, 221), (198, 202, 206)])
    background = np.full((bg_h, bg_w, 3), bg_color, dtype=np.uint8)
    page_np = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

    margin_x = rng.randint(35, max(45, int(bg_w * 0.08)))
    margin_y = rng.randint(35, max(45, int(bg_h * 0.07)))
    max_w = bg_w - margin_x * 2
    max_h = bg_h - margin_y * 2
    scale = min(max_w / src_w, max_h / src_h) * rng.uniform(0.92, 1.0)
    target_w = int(src_w * scale)
    target_h = int(src_h * scale)
    left = rng.randint(20, max(21, bg_w - target_w - 20))
    top = rng.randint(20, max(21, bg_h - target_h - 20))
    jitter = rng.randint(12, 46)
    dst = np.float32(
        [
            [left + rng.randint(-jitter, jitter), top + rng.randint(-jitter, jitter)],
            [left + target_w + rng.randint(-jitter, jitter), top + rng.randint(-jitter, jitter)],
            [left + target_w + rng.randint(-jitter, jitter), top + target_h + rng.randint(-jitter, jitter)],
            [left + rng.randint(-jitter, jitter), top + target_h + rng.randint(-jitter, jitter)],
        ]
    )
    src = np.float32([[0, 0], [src_w, 0], [src_w, src_h], [0, src_h]])
    matrix = cv2.getPerspectiveTransform(src, dst)

    shadow = background.copy()
    shadow_poly = (dst + np.array([rng.randint(8, 18), rng.randint(12, 28)], dtype=np.float32)).astype(np.int32)
    cv2.fillConvexPoly(shadow, shadow_poly, (150, 150, 150))
    background = cv2.addWeighted(shadow, 0.20, background, 0.80, 0)

    warped = cv2.warpPerspective(page_np, matrix, (bg_w, bg_h), borderValue=(0, 0, 0))
    mask = cv2.warpPerspective(np.full((src_h, src_w), 255, dtype=np.uint8), matrix, (bg_w, bg_h))
    mask3 = cv2.merge([mask, mask, mask])
    composed = np.where(mask3 > 0, warped, background)

    alpha = rng.uniform(0.90, 1.10)
    beta = rng.randint(-12, 12)
    composed = cv2.convertScaleAbs(composed, alpha=alpha, beta=beta)
    if rng.random() < 0.35:
        composed = cv2.GaussianBlur(composed, (3, 3), rng.uniform(0.15, 0.45))

    transformed: list[Box] = []
    for box in labels:
        corners = np.float32(
            [
                [[box.x1, box.y1]],
                [[box.x2, box.y1]],
                [[box.x2, box.y2]],
                [[box.x1, box.y2]],
            ]
        )
        points = cv2.perspectiveTransform(corners, matrix).reshape(-1, 2)
        x1 = float(np.clip(points[:, 0].min(), 0, bg_w - 1))
        y1 = float(np.clip(points[:, 1].min(), 0, bg_h - 1))
        x2 = float(np.clip(points[:, 0].max(), 0, bg_w - 1))
        y2 = float(np.clip(points[:, 1].max(), 0, bg_h - 1))
        transformed.append(Box(box.cls, x1, y1, x2, y2).clipped(bg_w, bg_h))

    rgb = cv2.cvtColor(composed, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb), dedupe_boxes(transformed)


def copy_remapped_existing(old_dataset: Path, output: Path) -> Counter:
    counts: Counter = Counter()
    for split in ("train", "val"):
        image_dir = old_dataset / "images" / split
        label_dir = old_dataset / "labels" / split
        if not image_dir.exists():
            continue
        for image_path in sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES):
            width, height = read_image_size(image_path)
            old_boxes = read_old_labels(label_dir / f"{image_path.stem}.txt", width, height)
            boxes = remap_existing_labels(old_boxes, width, height)
            out_name = f"real_{split}_{image_path.stem}{image_path.suffix.lower()}"
            out_image = output / "images" / split / out_name
            out_label = output / "labels" / split / f"{Path(out_name).stem}.txt"
            shutil.copy2(image_path, out_image)
            write_labels(out_label, boxes, width, height)
            counts.update(box.cls for box in boxes)
    return counts


def generate_real_augmented_train(old_dataset: Path, output: Path, augmentations_per_image: int, seed: int) -> Counter:
    counts: Counter = Counter()
    if augmentations_per_image <= 0:
        return counts
    image_dir = old_dataset / "images" / "train"
    label_dir = old_dataset / "labels" / "train"
    if not image_dir.exists():
        return counts
    for image_index, image_path in enumerate(sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)):
        width, height = read_image_size(image_path)
        old_boxes = read_old_labels(label_dir / f"{image_path.stem}.txt", width, height)
        boxes = remap_existing_labels(old_boxes, width, height)
        if not boxes:
            continue
        with Image.open(image_path) as image:
            source_image = image.convert("RGB")
        for aug_index in range(augmentations_per_image):
            rng = random.Random(seed + 3_000_000 + image_index * 997 + aug_index * 37)
            augmented, augmented_boxes = apply_phone_effect(source_image, boxes, rng)
            image_name = f"realaug_train_{image_index:04d}_{aug_index:02d}.jpg"
            image_out = output / "images" / "train" / image_name
            label_out = output / "labels" / "train" / f"{Path(image_name).stem}.txt"
            save_jpeg(augmented, image_out, rng)
            write_labels(label_out, augmented_boxes, augmented.width, augmented.height)
            counts.update(box.cls for box in augmented_boxes)
    return counts


def save_jpeg(image: Image.Image, path: Path, rng: random.Random) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "JPEG", quality=rng.randint(78, 93), optimize=True)


def generate_synthetic(output: Path, train_count: int, val_count: int, test_count: int, seed: int) -> Counter:
    counts: Counter = Counter()
    split_counts = {"train": train_count, "val": val_count, "test": test_count}
    split_offsets = {"train": 0, "val": 1_000_000, "test": 2_000_000}
    for split, total in split_counts.items():
        for index in range(total):
            rng = random.Random(seed + split_offsets[split] + index * 17)
            image, boxes = render_synthetic_page(split, index, rng)
            image_name = f"synthetic_{split}_{index:05d}.jpg"
            image_path = output / "images" / split / image_name
            label_path = output / "labels" / split / f"{Path(image_name).stem}.txt"
            save_jpeg(image, image_path, rng)
            write_labels(label_path, boxes, image.width, image.height)
            counts.update(box.cls for box in boxes)
    return counts


def write_data_yaml(output: Path) -> None:
    lines = [
        f"path: {output.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        "names:",
    ]
    for index, name in enumerate(CLASS_NAMES):
        lines.append(f"  {index}: {name}")
    (output / "data.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def average_hash(image_path: Path) -> int:
    with Image.open(image_path) as image:
        gray = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
        pixels = np.array(gray, dtype=np.float32)
    avg = pixels.mean()
    bits = pixels > avg
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bit)
    return value


def validate_dataset(output: Path) -> dict:
    summary: dict = {"splits": {}, "class_counts": Counter(), "duplicate_hashes": 0, "bad_labels": []}
    seen_hashes: dict[int, Path] = {}
    for split in ("train", "val", "test"):
        image_dir = output / "images" / split
        label_dir = output / "labels" / split
        images = sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
        labels = sorted(label_dir.glob("*.txt"))
        split_counter: Counter = Counter()
        for image_path in images:
            label_path = label_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                summary["bad_labels"].append(f"missing label: {image_path}")
                continue
            image_hash = average_hash(image_path)
            if image_hash in seen_hashes:
                summary["duplicate_hashes"] += 1
            else:
                seen_hashes[image_hash] = image_path
            for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
                parts = line.split()
                if len(parts) != 5:
                    summary["bad_labels"].append(f"{label_path}:{line_number}: expected 5 columns")
                    continue
                cls_id = int(float(parts[0]))
                coords = [float(value) for value in parts[1:]]
                if cls_id < 0 or cls_id >= len(CLASS_NAMES) or any(value < 0 or value > 1 for value in coords):
                    summary["bad_labels"].append(f"{label_path}:{line_number}: invalid value")
                    continue
                split_counter[cls_id] += 1
                summary["class_counts"][cls_id] += 1
        summary["splits"][split] = {"images": len(images), "labels": len(labels), "class_counts": dict(split_counter)}
    return summary


def write_manifest(material_root: Path, output: Path, args: argparse.Namespace, summary: dict) -> None:
    work_dir = material_root / "yolo_v2_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    manifest = work_dir / "dataset_manifest.tsv"
    with manifest.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(["field", "value"])
        writer.writerow(["dataset", str(output)])
        writer.writerow(["classes", ",".join(CLASS_NAMES)])
        writer.writerow(["synthetic_train", args.train_synthetic])
        writer.writerow(["synthetic_val", args.val_synthetic])
        writer.writerow(["synthetic_test", args.test_synthetic])
        writer.writerow(["real_augmentations_per_train_image", args.real_augmentations])
        writer.writerow(["seed", args.seed])
        writer.writerow(["duplicate_hashes", summary["duplicate_hashes"]])
        writer.writerow(["bad_label_count", len(summary["bad_labels"])])
    source_note = work_dir / "source_notes.md"
    source_note.write_text(
        "# YOLO v2 source notes\n\n"
        "- Existing local labeled screenshots were remapped from the original 9-class dataset.\n"
        "- Synthetic university question pages were generated locally for research training.\n"
        "- No external copyrighted image corpus is downloaded by this script.\n"
        "- Put manually authorized research images under this work directory before adding them to future dataset builds.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-synthetic", type=int, default=1200)
    parser.add_argument("--val-synthetic", type=int, default=500)
    parser.add_argument("--test-synthetic", type=int, default=300)
    parser.add_argument("--real-augmentations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260522)
    parser.add_argument("--output-name", default="训练数据集_v2_5class")
    args = parser.parse_args()

    root = repo_root()
    old_dataset = root / "训练数据集"
    material_root = root / "素材"
    output = root / args.output_name
    if not old_dataset.exists():
        raise FileNotFoundError(old_dataset)

    safe_reset_dir(output)
    for split in ("train", "val", "test"):
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)

    remapped_counts = copy_remapped_existing(old_dataset, output)
    real_augmented_counts = generate_real_augmented_train(old_dataset, output, args.real_augmentations, args.seed)
    synthetic_counts = generate_synthetic(output, args.train_synthetic, args.val_synthetic, args.test_synthetic, args.seed)
    write_data_yaml(output)
    summary = validate_dataset(output)
    write_manifest(material_root, output, args, summary)

    print(f"Dataset: {output}")
    print(f"Remapped counts: {dict(remapped_counts)}")
    print(f"Real augmented counts: {dict(real_augmented_counts)}")
    print(f"Synthetic counts: {dict(synthetic_counts)}")
    print(f"Splits: {summary['splits']}")
    print(f"Total class counts: {dict(summary['class_counts'])}")
    print(f"Duplicate perceptual hashes: {summary['duplicate_hashes']}")
    print(f"Bad labels: {len(summary['bad_labels'])}")
    if summary["bad_labels"]:
        for item in summary["bad_labels"][:20]:
            print(item)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
