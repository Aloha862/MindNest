from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FormulaItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    latex: str = ""
    description: str = ""


class NormalizedQuestion(BaseModel):
    model_config = ConfigDict(extra="allow")

    questionNo: str = ""
    title: str = ""
    content: str = ""
    stem: str = ""
    subject: str = "其他"
    chapter: str = ""
    questionType: str = "未知"
    knowledgePoints: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)
    difficulty: str = "基础"
    answer: str = ""
    answerConfidence: float = 0.0
    analysisSummary: str = ""
    detailedAnalysis: str = ""
    solutionSteps: list[str] = Field(default_factory=list)
    formulas: list[FormulaItem] = Field(default_factory=list)
    commonMistakes: list[str] = Field(default_factory=list)
    errorCauseTags: list[str] = Field(default_factory=list)
    reviewPlan: list[str] = Field(default_factory=list)
    similarPracticeSuggestions: list[str] = Field(default_factory=list)
    estimatedTime: str = ""
    sourceImageUrl: str = ""
    sourceBbox: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    needsReview: bool = False
    validationWarnings: list[str] = Field(default_factory=list)


class NormalizedVLMResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: str = ""
    layoutType: str = "unknown"
    materialType: str = "exam_question"
    questions: list[NormalizedQuestion] = Field(default_factory=list)
    needsReview: bool = False
    validationWarnings: list[str] = Field(default_factory=list)


def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [str(value)]


def _clean_list(value: Any) -> list[str]:
    result = []
    for item in _as_list(value):
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_formulas(value: Any) -> list[dict]:
    formulas = []
    for item in _as_list(value):
        if isinstance(item, dict):
            latex = str(item.get("latex") or item.get("text") or "").strip()
            if latex:
                formulas.append({**item, "latex": latex})
        else:
            latex = str(item or "").strip()
            if latex:
                formulas.append({"latex": latex, "description": ""})
    return formulas


def _infer_subject(text: str, subject_hint: str = "") -> str:
    if subject_hint:
        return subject_hint
    if any(marker in text for marker in ("函数", "导数", "积分", "方程", "证明", "几何", "概率", "矩阵")):
        return "数学"
    if any(marker in text.lower() for marker in ("english", "reading", "grammar", "translate")):
        return "英语"
    if any(marker in text for marker in ("电路", "力", "速度", "加速度", "电压")):
        return "物理"
    return "其他"


def _infer_question_type(text: str, options: list[str]) -> str:
    if options:
        return "选择题"
    if "填空" in text or "____" in text:
        return "填空题"
    if "证明" in text:
        return "证明题"
    if "简答" in text:
        return "简答题"
    if "计算" in text or "求" in text:
        return "解答题"
    return "未知"


def normalize_vlm_result(raw: dict, *, subject_hint: str = "", source_image_url: str = "") -> dict:
    warnings: list[str] = []
    raw_questions = raw.get("questions", [])
    if not isinstance(raw_questions, list):
        raw_questions = []
        warnings.append("VLM questions 不是数组，已置为空数组")

    questions: list[NormalizedQuestion] = []
    for index, item in enumerate(raw_questions, start=1):
        if not isinstance(item, dict):
            warnings.append(f"第 {index} 题不是对象，已跳过")
            continue
        content = str(item.get("content") or item.get("stem") or item.get("title") or "").strip()
        stem = str(item.get("stem") or content).strip()
        item_warnings = []
        if not content and not stem:
            warnings.append(f"第 {index} 题缺少题干，已跳过")
            continue
        options = _clean_list(item.get("options"))
        subject = str(item.get("subject") or "").strip()
        question_type = str(item.get("questionType") or item.get("question_type") or "").strip()
        if not subject:
            subject = _infer_subject(f"{content}\n{stem}", subject_hint)
            item_warnings.append("缺少学科，已自动推断")
        if not question_type:
            question_type = _infer_question_type(f"{content}\n{stem}", options)
            item_warnings.append("缺少题型，已自动推断")
        knowledge_points = _clean_list(item.get("knowledgePoints") or item.get("knowledge_points") or item.get("tags"))
        tags = _clean_list(item.get("tags") or knowledge_points)
        formulas = _normalize_formulas(item.get("formulas"))
        normalized = NormalizedQuestion(
            **{
                **item,
                "title": str(item.get("title") or item.get("questionNo") or f"题目 {index}").strip(),
                "content": content,
                "stem": stem,
                "subject": subject,
                "questionType": question_type,
                "knowledgePoints": knowledge_points,
                "tags": tags,
                "options": options,
                "difficulty": str(item.get("difficulty") or "基础").strip(),
                "answer": str(item.get("answer") or "").strip(),
                "analysisSummary": str(item.get("analysisSummary") or item.get("analysis") or "").strip(),
                "formulas": formulas,
                "sourceImageUrl": str(item.get("sourceImageUrl") or source_image_url or "").strip(),
                "answerConfidence": _float(item.get("answerConfidence"), 0.0),
                "confidence": _float(item.get("confidence") or item.get("answerConfidence"), 0.0),
                "needsReview": bool(item.get("needsReview")) or bool(item_warnings),
                "validationWarnings": item_warnings,
            }
        )
        questions.append(normalized)

    if not questions:
        warnings.append("VLM 未返回可落库题目")

    result = NormalizedVLMResult(
        summary=str(raw.get("summary") or "").strip(),
        layoutType=str(raw.get("layoutType") or raw.get("layout_type") or "unknown").strip(),
        materialType=str(raw.get("materialType") or raw.get("material_type") or "exam_question").strip(),
        questions=questions,
        needsReview=bool(warnings) or any(item.needsReview for item in questions),
        validationWarnings=warnings,
    )
    return result.model_dump()
