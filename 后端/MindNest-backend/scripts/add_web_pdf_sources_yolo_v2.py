# -*- coding: utf-8 -*-
"""Append public web/PDF question pages to the 5-class YOLO dataset.

This script only uses openly reachable URLs listed in SOURCE_URLS. It renders
PDF pages, creates weak layout labels from PDF text/image blocks, and optionally
adds phone-photo augmentations of those pages.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import fitz
import requests
from PIL import Image
from urllib3.exceptions import InsecureRequestWarning

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from prepare_yolo_v2_dataset import Box, apply_phone_effect, save_jpeg, write_labels  # noqa: E402


CLASS_NAMES = ["question", "diagram", "formula", "answer", "analysis"]
IMAGE_SUFFIX = ".jpg"

SOURCE_URLS = [
    {
        "id": "ztbu_higher_math",
        "subject": "高等数学",
        "url": "https://www.ztbu.edu.cn/uploadfile/files/2023/05/24/20230524091450040.pdf",
        "max_pages": 14,
    },
    {
        "id": "shisu_english_sample",
        "subject": "大学英语",
        "url": "https://zhaosheng.shisu.edu.cn/_upload/article/files/74/23/900d04a94b3c9d3a7cda9a7c9365/f6d833bd-202f-43df-bda1-e2d47d0773f0.pdf",
        "max_pages": 18,
    },
    {
        "id": "bnu_english_sample",
        "subject": "大学英语",
        "url": "https://bkzsw.bnu.edu.cn/docs/20221230120642708351.pdf",
        "max_pages": 14,
    },
    {
        "id": "ncut_english_sample",
        "subject": "大学英语",
        "url": "https://zs.ncut.edu.cn/__local/1/FC/63/5399F7650F4A85BB7A77BBA3319_C88FA4F1_31EF7.pdf",
        "max_pages": 12,
    },
    {
        "id": "xdf_cet4_mock",
        "subject": "大学英语",
        "url": "https://cq.xdf.cn/Portals/32/yh/j4d.pdf",
        "max_pages": 16,
    },
    {
        "id": "hfit_cet4_instruction",
        "subject": "大学英语",
        "url": "https://jwc.hfit.edu.cn/_upload/article/files/68/e1/2d01ffd544a0993d5c9145abb311/4572c723-1621-4bc0-93b9-d85a30d4a678.pdf",
        "max_pages": 12,
    },
    {
        "id": "gwng_cet4_answer",
        "subject": "大学英语",
        "url": "https://www-new.gwng.edu.cn/_upload/article/files/67/aa/f51a0dd1431eadc255d5fe3d531c/f94518f9-3ff0-43c0-bfe4-4188aa7cd78b.pdf",
        "max_pages": 18,
    },
    {
        "id": "fltrp_cet4_catalog",
        "subject": "大学英语",
        "url": "https://fltrp-gy.oss-cn-shanghai.aliyuncs.com/gykejianupload/20240303/files/%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD%E5%9B%9B%E7%BA%A7%E8%80%83%E8%AF%95%E7%9C%9F%E9%A2%98%E5%85%A8%E8%A7%A3%2B%E6%A0%87%E5%87%86%E9%A2%84%E6%B5%8B%28%E5%A4%87%E6%88%982024.06%29_-%E7%9B%AE%E5%BD%95.pdf",
        "max_pages": 8,
    },
    {
        "id": "ynnu_politics",
        "subject": "政治",
        "url": "https://smarx.ynnu.edu.cn/_upload/article/files/1a/8e/f29e56354618b9ba44e5d946e98e/92d1f871-d8ec-4b0a-bcfa-9e75574fc7ec.pdf",
        "max_pages": 18,
    },
    {
        "id": "jxufe_politics",
        "subject": "政治",
        "url": "https://marx.jxufe.edu.cn/upload/202501/02/202501021557123278.pdf",
        "max_pages": 18,
    },
]


@dataclass(frozen=True)
class PdfBlock:
    cls: int
    box: fitz.Rect
    text: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def download_pdf(url: str, output: Path) -> bool:
    output.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 MindNest research dataset builder",
        "Accept": "application/pdf,text/html,*/*",
    }
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    response = None
    errors = []
    for verify in (True, False):
        try:
            response = requests.get(url, headers=headers, timeout=45, allow_redirects=True, verify=verify)
            response.raise_for_status()
            break
        except Exception as exc:
            errors.append(repr(exc))
            response = None
    if response is None:
        print(f"download failed: {url} -> {' | '.join(errors)}")
        return False
    content = response.content
    if not content.startswith(b"%PDF"):
        print(f"skip non-pdf: {url} content-type={response.headers.get('content-type')}")
        return False
    output.write_bytes(content)
    return True


def classify_text(text: str) -> int:
    compact = re.sub(r"\s+", "", text)
    lower = text.lower()
    if not compact:
        return 0
    if re.search(r"(解析|解答|分析|证明|思路|参考解析|答案解析|solution|explanation)", compact, re.I):
        return 4
    if re.search(r"(答案|参考答案|正确答案|答[:：]|answer|key)", compact, re.I):
        return 3
    math_marks = sum(1 for ch in text if ch in "=+-×÷*/∫∑√≤≥<>∂∞≈≠{}[]()")
    latin_marks = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if math_marks >= 4 or ("O(" in text and ")" in text) or re.search(r"\b(log|lim|sin|cos|tan|det|rank)\b", lower):
        return 2
    return 0


def merge_nearby(blocks: list[PdfBlock], page_width: float, page_height: float) -> list[PdfBlock]:
    if not blocks:
        return []
    blocks = sorted(blocks, key=lambda item: (item.cls, item.box.y0, item.box.x0))
    merged: list[PdfBlock] = []
    for block in blocks:
        if block.box.width < page_width * 0.08 or block.box.height < page_height * 0.006:
            continue
        if not merged or merged[-1].cls != block.cls:
            merged.append(block)
            continue
        last = merged[-1]
        same_column = not (block.box.x0 > last.box.x1 + page_width * 0.05 or last.box.x0 > block.box.x1 + page_width * 0.05)
        vertical_close = block.box.y0 <= last.box.y1 + page_height * 0.025
        if same_column and vertical_close:
            merged[-1] = PdfBlock(last.cls, last.box | block.box, f"{last.text}\n{block.text}")
        else:
            merged.append(block)
    return merged


def page_blocks(page: fitz.Page) -> list[PdfBlock]:
    data = page.get_text("dict")
    blocks: list[PdfBlock] = []
    page_rect = page.rect
    for raw in data.get("blocks", []):
        bbox = fitz.Rect(raw.get("bbox"))
        if bbox.is_empty or bbox.width < 12 or bbox.height < 8:
            continue
        if raw.get("type") == 1:
            blocks.append(PdfBlock(1, bbox, "image"))
            continue
        lines = []
        for line in raw.get("lines", []):
            spans = [span.get("text", "") for span in line.get("spans", [])]
            line_text = "".join(spans).strip()
            if line_text:
                lines.append(line_text)
        text = "\n".join(lines).strip()
        if len(re.sub(r"\s+", "", text)) < 3:
            continue
        blocks.append(PdfBlock(classify_text(text), bbox, text))
    return merge_nearby(blocks, page_rect.width, page_rect.height)


def fitz_box_to_pixel(box: fitz.Rect, scale: float, cls: int, image_width: int, image_height: int) -> Box:
    pad_x = 6
    pad_y = 5
    return Box(
        cls,
        box.x0 * scale - pad_x,
        box.y0 * scale - pad_y,
        box.x1 * scale + pad_x,
        box.y1 * scale + pad_y,
    ).clipped(image_width, image_height)


def render_pdf_pages(source: dict, pdf_path: Path, dataset: Path, work_dir: Path, dpi: int, augment: int) -> list[dict]:
    records: list[dict] = []
    doc = fitz.open(pdf_path)
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    total = min(len(doc), int(source["max_pages"]))
    for page_index in range(total):
        page = doc[page_index]
        weak_blocks = page_blocks(page)
        if not weak_blocks:
            continue
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        labels = [
            fitz_box_to_pixel(block.box, scale, block.cls, image.width, image.height)
            for block in weak_blocks
        ]
        if not labels or not any(label.cls == 0 for label in labels):
            continue

        base_name = f"webpdf_{source['id']}_{page_index + 1:03d}"
        image_path = dataset / "images" / "train" / f"{base_name}{IMAGE_SUFFIX}"
        label_path = dataset / "labels" / "train" / f"{base_name}.txt"
        save_jpeg(image, image_path, __import__("random").Random(10_000 + page_index))
        write_labels(label_path, labels, image.width, image.height)
        records.append({"source": source["id"], "page": page_index + 1, "kind": "render", "image": str(image_path)})

        for aug_index in range(augment):
            rng = __import__("random").Random(50_000 + page_index * 97 + aug_index * 11 + hash(source["id"]) % 1000)
            augmented, augmented_labels = apply_phone_effect(image, labels, rng)
            aug_name = f"{base_name}_phone_{aug_index:02d}"
            aug_image = dataset / "images" / "train" / f"{aug_name}{IMAGE_SUFFIX}"
            aug_label = dataset / "labels" / "train" / f"{aug_name}.txt"
            save_jpeg(augmented, aug_image, rng)
            write_labels(aug_label, augmented_labels, augmented.width, augmented.height)
            records.append({"source": source["id"], "page": page_index + 1, "kind": "phone", "image": str(aug_image)})
    doc.close()
    return records


def write_manifest(work_dir: Path, records: list[dict], sources: list[dict]) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    with (work_dir / "web_pdf_sources.tsv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "subject", "url", "max_pages"], delimiter="\t")
        writer.writeheader()
        writer.writerows(sources)
    with (work_dir / "web_pdf_rendered_images.tsv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["source", "page", "kind", "image"], delimiter="\t")
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(repo_root() / "训练数据集_v2_5class"))
    parser.add_argument("--augment", type=int, default=3)
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args()

    root = repo_root()
    dataset = Path(args.dataset)
    work_dir = root / "素材" / "yolo_v2_work" / "web_pdf_sources"
    pdf_dir = work_dir / "pdfs"
    if not dataset.exists():
        raise FileNotFoundError(dataset)

    records: list[dict] = []
    for source in SOURCE_URLS:
        parsed = urlparse(source["url"])
        suffix = Path(parsed.path).suffix or ".pdf"
        pdf_path = pdf_dir / f"{source['id']}{suffix}"
        if not pdf_path.exists() and not download_pdf(source["url"], pdf_path):
            continue
        try:
            rendered = render_pdf_pages(source, pdf_path, dataset, work_dir, args.dpi, args.augment)
        except Exception as exc:
            print(f"render failed: {source['id']} -> {exc!r}")
            continue
        records.extend(rendered)
        print(f"{source['id']}: rendered {len(rendered)} images")

    write_manifest(work_dir, records, SOURCE_URLS)
    print(f"Rendered images appended: {len(records)}")
    print(f"Manifest: {work_dir}")


if __name__ == "__main__":
    main()
