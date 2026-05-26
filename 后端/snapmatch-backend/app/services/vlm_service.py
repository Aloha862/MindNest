from __future__ import annotations

from app.config import settings
from app.services.vision_model_client import (
    call_vision_model,
    current_vision_model_name,
    is_real_vision_provider,
    is_vision_model_configured,
)


def _layout_prompt(layout_context: dict | None) -> str:
    """Compress YOLO detections into text context for the VLM prompt."""
    if not layout_context:
        return "无"
    detections = layout_context.get("detections", [])[:20]
    items = []
    for item in detections:
        label = item.get("labelName") or item.get("label") or "unknown"
        confidence = float(item.get("confidence", 0) or 0)
        box = item.get("bbox") or item.get("box", {}) or {}
        items.append(
            f"{label}({confidence:.2f}) "
            f"x={box.get('x', 0)}, y={box.get('y', 0)}, "
            f"w={box.get('width', 0)}, h={box.get('height', 0)}"
        )
    return "\n".join(items) if items else "无"


def _ocr_preview(ocr_context: str | dict) -> str:
    if isinstance(ocr_context, dict):
        return str(ocr_context.get("mergedText") or ocr_context.get("rawText") or "")[:100]
    return str(ocr_context or "")[:100]


def _context_prompt(ocr_context: str | dict, layout_context: dict | None) -> str:
    if not isinstance(ocr_context, dict):
        return f"OCR 文本：\n{ocr_context}"
    quality = ocr_context.get("quality") or {}
    formula_blocks = ocr_context.get("formulaBlocks") or []
    ocr_blocks = ocr_context.get("blocks") or []
    merged_text = ocr_context.get("mergedText") or ocr_context.get("rawText") or ""
    return f"""
图像质量：
{quality}

版面区域：
{_layout_prompt(layout_context)}

OCR 文本块数量：{len(ocr_blocks)}
公式块数量：{len(formula_blocks)}

OCR/公式融合文本：
{merged_text}

公式块：
{formula_blocks[:20]}
"""


def _mock_vlm(image_path: str, ocr_text: str | dict, layout_context: dict | None = None) -> dict:
    # Mock VLM is only for frontend/backend integration. It keeps the workflow
    # runnable when the real multimodal model is not configured.
    return {
        "summary": "本图片包含 1 道数学选择题，主要考查函数奇偶性、导数性质和变上限积分的奇偶性判断。",
        "layoutType": (layout_context or {}).get("layoutType", "single_question"),
        "materialType": "exam_question",
        "questions": [
            {
                "questionNo": "例 9.24",
                "title": "连续导数与积分奇偶性判断",
                "content": "设函数 f(x) 在 (-∞,+∞) 上具有连续导数，判断含有 cos f(t)、f'(t) 的积分表达式的奇偶性。",
                "stem": "设函数 f(x) 在 (-∞,+∞) 上具有连续导数，则下列命题中正确的是哪一项。",
                "subject": "数学",
                "chapter": "高等数学/定积分与函数性质",
                "questionType": "选择题",
                "knowledgePoints": ["函数奇偶性", "导数", "复合函数", "变上限积分"],
                "tags": ["奇偶性", "定积分", "导数", "选择题"],
                "options": [
                    "A. 某积分表达式为奇函数",
                    "B. 某积分表达式为偶函数",
                    "C. 另一积分表达式为奇函数",
                    "D. 另一积分表达式为偶函数",
                ],
                "difficulty": "中等",
                "answer": "",
                "answerConfidence": 0.35,
                "analysisSummary": "需要结合函数奇偶性、导数奇偶变化规律和变上限积分性质逐项判断；mock 模式不强行给出确定答案。",
                "detailedAnalysis": "先从题干识别函数条件，再分别判断 cos f(t)、f'(t) 及其组合的奇偶性。对于变上限积分，需要利用被积函数在关于 0 对称区间上的性质判断新函数的奇偶性。若 OCR 未完整识别选项，标准答案应保留为空，避免编造。",
                "solutionSteps": [
                    "提取题干条件，明确 f(x) 的定义域、连续可导性以及题目给出的奇偶性条件。",
                    "根据函数奇偶性推导 f'(x) 的奇偶性变化规律。",
                    "判断 cos f(t) 与 f'(t) 组合后的被积函数性质。",
                    "使用变上限积分的奇偶性判定规则逐项验证选项。",
                    "将推导结果与 A、B、C、D 四个选项比对，得到最终答案。",
                ],
                "formulas": [
                    {
                        "latex": r"\int_0^x [\cos f(t)+f'(t)]\,dt",
                        "description": "变上限积分表达式",
                    },
                    {"latex": r"\cos(-u)=\cos u", "description": "余弦函数为偶函数"},
                ],
                "commonMistakes": [
                    "把 f(x) 的奇偶性直接等同于 f'(x) 的奇偶性",
                    "忽略变上限积分会改变函数奇偶性判断方式",
                    "只看局部公式，没有逐项代入选项",
                ],
                "errorCauseTags": ["概念混淆", "公式性质不熟", "审题不完整"],
                "reviewPlan": [
                    "当天复习函数奇偶性与导数奇偶性关系",
                    "3 天后练习变上限积分奇偶性题",
                    "7 天后完成同知识点综合选择题",
                ],
                "similarPracticeSuggestions": [
                    "查找 2 道函数奇偶性与导数关系题",
                    "查找 2 道变上限积分性质题",
                ],
                "estimatedTime": "6-8 分钟",
                "sourceImageUrl": "",
            }
        ],
        "debug": {
            "provider": "mock",
            "imagePath": image_path,
            "ocrPreview": _ocr_preview(ocr_text),
            "layoutDetections": len((layout_context or {}).get("detections", [])),
        },
    }


def get_vlm_model_name() -> str:
    return current_vision_model_name()


def analyze_question(image_path: str, ocr_context: str | dict, layout_context: dict | None = None) -> dict:
    if not is_real_vision_provider(settings.vlm_provider):
        return _mock_vlm(image_path, ocr_context, layout_context)
    if not is_vision_model_configured():
        raise RuntimeError(
            "VLM_PROVIDER 已配置为真实模型，但 DASHSCOPE_API_KEY/VLM_API_KEY、VLM_API_BASE、VLM_MODEL_NAME 不完整，请检查 .env 并重启后端。"
        )

    prompt = f"""
你是“面向学习场景的多模态智能题目理解与个性化复习平台”的题目理解引擎。

任务：
根据图片、图像质量、版面区域、OCR 文本块、公式块和 OCR/公式融合文本，完成题目区域理解、题干解析、答案推理、知识点归因、常见错误分析和个性化复习建议。

严格要求：
1. 只返回 JSON，不要返回 Markdown，不要解释 JSON 外的内容。
2. 不要编造图片中不存在的题目；看不清的字段填空字符串或空数组。
3. 如果图片包含多道题，questions 数组必须拆成多条题目。
4. OCR 可能有错误，图片内容优先，其次参考 OCR 文本、公式块和版面区域。
5. 数学公式必须尽量输出 LaTeX，优先吸收公式块中的 latex，放入 formulas 数组。
6. 如果无法确定标准答案，answer 为空，answerConfidence 小于 0.5，并在 analysisSummary 说明原因。
7. 输出要服务学习闭环，不能只给题目摘要；必须包含知识点、易错点、复习计划和相似练习建议。

结构化识别上下文：
{_context_prompt(ocr_context, layout_context)}

返回 JSON 结构：
{{
  "summary": "整张图片的内容摘要，说明题目数量、科目、主要考点",
  "layoutType": "single_question|multi_question|note|unknown",
  "materialType": "exam_question|homework|mistake|note|learning_material",
  "questions": [
    {{
      "questionNo": "题号",
      "title": "题目标题",
      "content": "完整题目内容",
      "stem": "题干，不包含选项",
      "subject": "数学|英语|计算机|政治|专业课|物理|其他",
      "chapter": "章节或模块",
      "questionType": "选择题|填空题|解答题|证明题|简答题|综合题|未知",
      "knowledgePoints": ["知识点1", "知识点2"],
      "tags": ["标签1", "标签2"],
      "options": ["A. ...", "B. ..."],
      "difficulty": "基础|中等|较难",
      "answer": "参考答案，无法判断则为空",
      "answerConfidence": 0.0,
      "analysisSummary": "一句话解析摘要",
      "detailedAnalysis": "较完整的解题思路和推理说明",
      "solutionSteps": ["步骤1", "步骤2", "步骤3"],
      "formulas": [
        {{"latex": "公式 LaTeX", "description": "公式含义"}}
      ],
      "commonMistakes": ["常见错误1", "常见错误2"],
      "errorCauseTags": ["概念不清|计算错误|审题错误|公式使用错误"],
      "reviewPlan": ["当天复习建议", "3天后复习建议", "7天后复习建议"],
      "similarPracticeSuggestions": ["同知识点练习建议1", "同难度练习建议2"],
      "estimatedTime": "预计用时",
      "sourceImageUrl": ""
    }}
  ]
}}
"""
    prompt = f"""
你是“面向学习场景的多模态智能题目理解与个性化复习平台”的题目理解引擎。

任务：
根据图片、OCR 文本、YOLO 版面区域和公式候选，完成题目结构化理解、答案推理、知识点归因、易错点分析和个性化复习建议。

严格要求：
1. 只返回 JSON，不返回 Markdown，不解释 JSON 之外的内容。
2. 不要编造图片中不存在的题目；看不清的字段填空字符串或空数组。
3. OCR 可能有错误，图片内容优先，其次参考 OCR 文本、公式块和版面区域。
4. 所有数学公式必须使用标准 LaTeX。公式内部禁止换行，禁止把同一个积分式拆成多段。
5. 复杂公式请放入 formulas 数组，latex 字段只写纯 LaTeX，不要带 `$`、`$$`、Markdown 或中文说明。
6. detailedAnalysis 和 solutionSteps 中如果包含公式，用 `$...$` 包裹短公式；长积分、分式、根式尽量完整写在同一个 `$...$` 内。
7. 对带上下限的积分，必须写成 `\\int_{{下限}}^{{上限}}`，例如 `\\int_{{1/2}}^{{3/2}} \\frac{{dx}}{{\\sqrt{{|x-x^2|}}}}`。
8. 如果无法确定标准答案，answer 为空，answerConfidence 小于 0.5，并在 analysisSummary 说明原因。

结构化识别上下文：
{_context_prompt(ocr_context, layout_context)}

返回 JSON 结构：
{{
  "summary": "整张图片的内容摘要，说明题目数量、科目和主要考点",
  "layoutType": "single_question|multi_question|note|unknown",
  "materialType": "exam_question|homework|mistake|note|learning_material",
  "questions": [
    {{
      "questionNo": "题号",
      "title": "题目标题",
      "content": "完整题目内容",
      "stem": "题干，不包含选项",
      "subject": "数学|英语|计算机|政治|专业课|物理|其他",
      "chapter": "章节或模块",
      "questionType": "选择题|填空题|解答题|证明题|简答题|综合题|未知",
      "knowledgePoints": ["知识点"],
      "tags": ["标签"],
      "options": ["A. ...", "B. ..."],
      "difficulty": "基础|中等|较难",
      "answer": "参考答案，无法判断则为空",
      "answerConfidence": 0.0,
      "analysisSummary": "一句话解析摘要",
      "detailedAnalysis": "较完整的解题思路和推理说明，公式必须使用单行 LaTeX",
      "solutionSteps": ["步骤1", "步骤2", "步骤3"],
      "formulas": [
        {{"latex": "公式 LaTeX", "description": "公式含义"}}
      ],
      "commonMistakes": ["常见错误1", "常见错误2"],
      "errorCauseTags": ["概念不清|计算错误|审题错误|公式使用错误"],
      "reviewPlan": ["当天复习建议", "3天后复习建议", "7天后复习建议"],
      "similarPracticeSuggestions": ["同知识点练习建议1", "同难度练习建议"],
      "estimatedTime": "预计用时",
      "sourceImageUrl": ""
    }}
  ]
}}
"""
    result = call_vision_model(image_path, prompt, timeout=75)
    result.setdefault("summary", "")
    result.setdefault("layoutType", "")
    result.setdefault("materialType", "exam_question")
    result.setdefault("questions", [])
    result["debug"] = {
        "provider": current_vision_model_name(),
        "ocrPreview": _ocr_preview(ocr_context),
        "layoutDetections": len((layout_context or {}).get("detections", [])),
    }
    return result
