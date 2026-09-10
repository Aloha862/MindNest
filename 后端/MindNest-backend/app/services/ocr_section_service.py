import re


QUESTION_RE = re.compile(r"^(题|题目|例|例题|例\s*\d|已知|设|设有|求|证明|判断|判别|若|如图|计算|求证|★★)")
ANALYSIS_RE = re.compile(r"^(分析|解析|思路|方法|注意|提示|解题思路|考点)")
ANSWER_RE = re.compile(r"^(解|答案|答|故|所以|因此|综上|应选|选|正确答案)")
OPTION_RE = re.compile(r"^[A-Da-d][.．、)]")
SUB_QUESTION_RE = re.compile(r"^[(（]?\d+[)）.、]")


def _clean_title_text(line: str) -> str:
    return line.strip().replace("：", ":")


def _line_type(line: str, current_type: str | None = None) -> tuple[str, str] | None:
    text = _clean_title_text(line)
    if not text:
        return None
    if ANALYSIS_RE.match(text):
        return "analysis", "分析/解析"
    if ANSWER_RE.match(text):
        return "answer", "答案/解答"
    if SUB_QUESTION_RE.match(text):
        number = re.findall(r"\d+", text)[0]
        return "sub_question", f"第{number}小问"
    if OPTION_RE.match(text):
        return "option", "选项"
    if QUESTION_RE.match(text):
        return "stem", "题干"
    # 公式行跟随当前语义块，不再单独切成“公式区域”。
    if current_type in {"analysis", "answer", "stem", "sub_question", "option"}:
        return current_type, {
            "analysis": "分析/解析",
            "answer": "答案/解答",
            "stem": "题干",
            "sub_question": "小问",
            "option": "选项",
        }[current_type]
    return None


def _should_start_new_section(current: dict | None, next_type: str) -> bool:
    if current is None:
        return True
    current_type = current["type"]
    if next_type == current_type:
        return False
    if next_type in {"stem", "analysis", "answer", "sub_question", "option"}:
        return True
    return False


def build_ocr_sections(
    raw_text: str,
    blocks: list[dict] | None = None,
    formula_blocks: list[dict] | None = None,
    layout_blocks: list[dict] | None = None,
) -> list[dict]:
    lines = [line.strip() for line in re.split(r"[\r\n]+", raw_text or "") if line.strip()]
    if not lines and blocks:
        lines = [str(item.get("text", "")).strip() for item in blocks if str(item.get("text", "")).strip()]

    sections: list[dict] = []
    current: dict | None = None

    def start_section(section_type: str, title: str) -> None:
        nonlocal current
        current = {"type": section_type, "title": title, "lines": []}
        sections.append(current)

    for index, line in enumerate(lines, start=1):
        marker = _line_type(line, current["type"] if current else None)
        if marker:
            section_type, title = marker
            if _should_start_new_section(current, section_type):
                start_section(section_type, title)
        elif current is None:
            start_section("stem", "题干")
        current["lines"].append({"lineNo": index, "text": line})

    if not sections:
        sections.append({"type": "empty", "title": "识别文本", "lines": []})
    return sections
