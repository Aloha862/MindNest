from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path

from app.config import settings


REAL_VISION_PROVIDERS = {"qwen", "dashscope", "aliyun", "tongyi"}


def _api_key() -> str:
    # Compatible with Aliyun Bailian examples and this project's .env naming.
    return settings.dashscope_api_key or settings.vlm_api_key


def is_real_vision_provider(provider: str | None = None) -> bool:
    value = (provider or settings.vlm_provider).lower().strip()
    return value in REAL_VISION_PROVIDERS or value == "vlm"


def is_vision_model_configured(provider: str | None = None, model_name: str | None = None) -> bool:
    provider_value = (provider or settings.vlm_provider).lower().strip()
    model_value = model_name or settings.vlm_model_name
    return provider_value in REAL_VISION_PROVIDERS and bool(_api_key() and settings.vlm_api_base and model_value)


def current_vision_model_name() -> str:
    if is_vision_model_configured():
        return f"{settings.vlm_provider}:{settings.vlm_model_name}"
    return "mock-vlm-v1"


def image_to_data_url(image_path: str) -> str:
    path = Path(image_path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _escape_loose_json_backslashes(content: str) -> str:
    """Make model JSON with raw LaTeX backslashes parseable."""
    output: list[str] = []
    in_string = False
    index = 0
    while index < len(content):
        char = content[index]
        if not in_string:
            output.append(char)
            if char == '"':
                in_string = True
            index += 1
            continue

        if char == '"':
            output.append(char)
            in_string = False
            index += 1
            continue

        if char == "\r":
            if index + 1 < len(content) and content[index + 1] == "\n":
                index += 1
            output.append("\\n")
            index += 1
            continue

        if char == "\n":
            output.append("\\n")
            index += 1
            continue

        if char == "\t":
            output.append("\\t")
            index += 1
            continue

        if char != "\\":
            output.append(char)
            index += 1
            continue

        next_char = content[index + 1] if index + 1 < len(content) else ""
        if next_char in {'"', "\\", "/"}:
            output.append(char)
            output.append(next_char)
            index += 2
            continue
        if next_char == "u" and re.match(r"^u[0-9a-fA-F]{4}", content[index + 1 : index + 6]):
            output.append(content[index : index + 6])
            index += 6
            continue

        output.append("\\\\")
        index += 1
    return "".join(output)


def extract_json_object(text: str):
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)

    candidates = [content]
    escaped_content = _escape_loose_json_backslashes(content)
    if escaped_content != content:
        candidates.append(escaped_content)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, (dict, list)):
                return parsed
            raise ValueError("模型返回的 JSON 不是对象或数组")
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    for candidate in candidates:
        for index, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(candidate[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, (dict, list)):
                return parsed

    raise ValueError(f"模型未返回可解析 JSON 对象或数组：{text[:200]}")


def _collect_stream_response(completion) -> str:
    content_parts: list[str] = []
    for chunk in completion:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        piece = getattr(delta, "content", None)
        if piece:
            content_parts.append(piece)
    return "".join(content_parts)


def _strip_markdown_fence(text: str) -> str:
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json|markdown|md)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)
    return content.strip()


def call_vision_model(
    image_path: str,
    prompt: str,
    *,
    timeout: int = 90,
    model_name: str | None = None,
    include_thinking: bool = True,
    fallback_text_field: str | None = None,
):
    """Call Aliyun Bailian / DashScope OpenAI-compatible vision chat completion."""
    target_model = model_name or settings.vlm_model_name
    if not is_vision_model_configured(model_name=target_model):
        raise RuntimeError("未配置真实视觉模型，请检查 VLM_PROVIDER、DASHSCOPE_API_KEY/VLM_API_KEY、VLM_API_BASE 和模型名称")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("缺少 openai 依赖，请先执行：pip install openai") from exc

    client = OpenAI(api_key=_api_key(), base_url=settings.vlm_api_base, timeout=timeout)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}},
            ],
        }
    ]
    extra_body = {"enable_thinking": settings.vlm_enable_thinking} if include_thinking else {}

    try:
        request_payload = {
            "model": target_model,
            "messages": messages,
            "stream": settings.vlm_stream,
            "temperature": 0.1,
        }
        if extra_body:
            request_payload["extra_body"] = extra_body
        completion = client.chat.completions.create(**request_payload)
        if settings.vlm_stream:
            content = _collect_stream_response(completion)
        else:
            message = completion.choices[0].message
            content = message.content or ""
    except Exception as exc:
        raise RuntimeError(f"视觉模型接口调用失败：{exc}") from exc

    if not content:
        raise RuntimeError("视觉模型返回为空")

    try:
        return extract_json_object(content)
    except Exception as first_error:
        if fallback_text_field and not content.lstrip().startswith("{"):
            text = _strip_markdown_fence(content)
            return {
                fallback_text_field: text,
                "blocks": [
                    {
                        "text": text,
                        "confidence": 0.85,
                        "box": {"x": 0, "y": 0, "width": 0, "height": 0},
                        "source": "vision-text-fallback",
                    }
                ],
                "formulaBlocks": [],
            }
        if settings.vlm_json_repair_retry <= 0:
            raise

        repair_prompt = (
            "请把下面的模型输出修复为合法 JSON 对象。只返回 JSON，不要 Markdown，不要解释。\n"
            "如果字段缺失，请保留可恢复字段，并用空字符串、空数组或空对象补齐。\n\n"
            f"{content}"
        )
        repair_model = settings.vlm_model_name or target_model
        try:
            repaired = client.chat.completions.create(
                model=repair_model,
                messages=[{"role": "user", "content": repair_prompt}],
                stream=False,
                temperature=0,
            )
            repaired_content = repaired.choices[0].message.content or ""
            return extract_json_object(repaired_content)
        except Exception as repair_error:
            raise ValueError(f"VLM 返回 JSON 非法，修复失败：{first_error}; {repair_error}") from repair_error
