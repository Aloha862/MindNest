from __future__ import annotations

import json
import threading
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.exceptions import AppException
from app.models.model_log import ModelLog
from app.models.question import Question
from app.models.recognition_task import RecognitionTask
from app.models.upload_file import UploadFile
from app.models.user import User
from app.schemas.recognition import RecognitionBatchStartRequest, RecognitionStartRequest
from app.services import material_service
from app.services.file_service import get_file_or_404
from app.services.formula_service import detect_formulas, merge_text_and_formula_blocks
from app.services.image_service import assess_image_quality, preprocess_image
from app.services.model_log_service import create_model_log
from app.services.ocr_section_service import build_ocr_sections
from app.services.ocr_service import get_ocr_model_name, run_ocr
from app.services.serializers import file_out, parse_json_dict, parse_json_list, question_out, task_out
from app.services.vlm_normalizer import normalize_vlm_result
from app.services.vlm_service import analyze_question, get_vlm_model_name
from app.services.yolo_service import detect_layout
from app.utils.file_utils import path_to_upload_url
from app.utils.pagination import paginate
from app.utils.time_utils import now


TASK_LOCK = threading.Semaphore(max(1, settings.max_concurrent_recognition))
TERMINAL_STATUSES = {"completed", "failed", "needs_review"}


class PipelineError(Exception):
    def __init__(self, message: str, *, error_code: str, error_stage: str):
        super().__init__(message)
        self.error_code = error_code
        self.error_stage = error_stage


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _stage_message(stage: str) -> str:
    return {
        "pending": "等待识别",
        "preprocessing": "OpenCV 图像质量评估与预处理中",
        "yolo_running": "版面区域检测中",
        "ocr_running": "OCR 文字识别中",
        "formula_running": "公式识别与文本融合中",
        "vlm_running": "VLM 结构化理解中",
        "parsing": "结构化结果校验中",
        "persisting": "题目卡片写入中",
        "completed": "识别完成",
        "needs_review": "识别完成，建议复核",
        "failed": "识别失败",
    }.get(stage, stage)


def _set_task(db: Session, task: RecognitionTask, status: str, progress: int, step: str | None = None) -> None:
    task.status = status
    task.current_step = step or _stage_message(status)
    task.progress = progress
    task.heartbeat_at = now()
    db.commit()
    db.refresh(task)


def _fail_task(
    db: Session,
    task: RecognitionTask,
    file: UploadFile | None,
    *,
    error_code: str,
    error_stage: str,
    message: str,
) -> None:
    task.status = "failed"
    task.current_step = _stage_message("failed")
    task.error_code = error_code
    task.error_stage = error_stage
    task.error_message = message
    task.finished_at = now()
    task.heartbeat_at = now()
    if file:
        file.status = "failed"
    create_model_log(
        db,
        task_id=task.id,
        model_type="system",
        model_name="recognition-pipeline",
        stage=error_stage,
        error_code=error_code,
        output_summary="识别流水线失败",
        status="failed",
        error_message=message,
    )
    db.commit()


def _run_stage(db: Session, task: RecognitionTask, stage: str, progress: int, fn):
    _set_task(db, task, stage, progress)
    start = perf_counter()
    try:
        result = fn()
        task.heartbeat_at = now()
        db.commit()
        return result
    except PipelineError:
        raise
    except Exception as exc:
        cost = int((perf_counter() - start) * 1000)
        message = str(exc)
        error_code = {
            "preprocessing": "PREPROCESS_FAILED",
            "yolo_running": "LAYOUT_FAILED",
            "formula_running": "FORMULA_FAILED",
            "parsing": "VLM_INVALID_JSON",
            "persisting": "DB_WRITE_FAILED",
        }.get(stage, f"{stage.upper()}_FAILED")
        if stage == "vlm_running":
            lowered = message.lower()
            if "timeout" in lowered or "timed out" in lowered or "超时" in message:
                error_code = "VLM_TIMEOUT"
            elif "json" in lowered:
                error_code = "VLM_INVALID_JSON"
            else:
                error_code = "VLM_EMPTY_RESULT"
        create_model_log(
            db,
            task_id=task.id,
            model_type="system",
            model_name=f"{stage}-stage",
            stage=stage,
            error_code=error_code,
            output_summary=f"{stage} 阶段异常",
            status="failed",
            cost_time=cost,
            error_message=message,
        )
        raise PipelineError(message, error_code=error_code, error_stage=stage) from exc


def _question_tags(item: dict) -> list[str]:
    values = []
    for key in ("knowledgePoints", "tags"):
        for value in item.get(key) or []:
            if value and value not in values:
                values.append(value)
    return values


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


def _normalize_blocks(blocks: list[dict]) -> list[dict]:
    normalized = []
    for item in blocks or []:
        if not isinstance(item, dict):
            continue
        box = _bbox(item)
        normalized.append({**item, "bbox": box, "box": box})
    return normalized


def _normalize_formula_blocks(blocks: list[dict], source: str) -> list[dict]:
    normalized = []
    for item in blocks or []:
        if not isinstance(item, dict):
            continue
        latex = str(item.get("latex") or item.get("text") or "").strip()
        if not latex:
            continue
        box = _bbox(item)
        normalized.append(
            {
                **item,
                "latex": latex,
                "text": str(item.get("text") or latex),
                "confidence": float(item.get("confidence", 0.75) or 0.75),
                "bbox": box,
                "box": box,
                "source": item.get("source") or source,
            }
        )
    return normalized


def _dedupe_formula_blocks(blocks: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for item in blocks:
        key = (item.get("latex", ""), tuple(_bbox(item).values()))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _avg_confidence(blocks: list[dict]) -> float:
    scores = [float(item.get("confidence", 0) or 0) for item in blocks if isinstance(item, dict)]
    return sum(scores) / len(scores) if scores else 0.0


def _create_questions(db: Session, task: RecognitionTask, file: UploadFile, normalized_result: dict, raw_result: dict) -> list[Question]:
    created: list[Question] = []
    task_needs_review = bool(normalized_result.get("needsReview")) or bool(normalized_result.get("validationWarnings"))
    for item in normalized_result.get("questions", []):
        source_url = item.get("sourceImageUrl") or file.file_url
        title = item.get("title") or f"题目 {item.get('questionNo', '')}".strip() or "未命名题目"
        tags = _question_tags(item)
        confidence = float(item.get("confidence", 0) or 0)
        review_status = "pending" if task_needs_review or confidence < 0.65 else "approved"
        question = Question(
            task_id=task.id,
            file_id=file.id,
            user_id=file.user_id,
            title=title,
            content=item.get("content") or item.get("stem") or title,
            subject=item.get("subject", "其他"),
            question_type=item.get("questionType", "未知"),
            knowledge_points=_dump(tags),
            options_json=item.get("options") or [],
            knowledge_points_json=tags,
            formulas_json=item.get("formulas") or [],
            raw_vlm_json=item,
            source_bbox_json=item.get("sourceBbox") or {},
            confidence=confidence,
            review_status=review_status,
            difficulty=item.get("difficulty", "基础"),
            answer=item.get("answer", ""),
            analysis_summary=item.get("analysisSummary", ""),
            source_image_url=source_url,
        )
        db.add(question)
        created.append(question)
    return created


def _merge_stored_question_data(stored_questions: list[dict], saved_questions: list[Question]) -> list[dict]:
    if not saved_questions:
        return stored_questions
    merged = []
    for index, question in enumerate(saved_questions):
        base = question_out(question)
        rich = stored_questions[index] if index < len(stored_questions) and isinstance(stored_questions[index], dict) else {}
        merged.append({**rich, **base})
    return merged


def _create_material(db: Session, task: RecognitionTask, file: UploadFile, vlm_result: dict) -> None:
    material_service.create_material(
        db,
        user_id=file.user_id,
        file_id=file.id,
        task_id=task.id,
        title=file.file_name,
        category=file.file_type or vlm_result.get("materialType", "note"),
        summary=vlm_result.get("summary", "") or task.ocr_text[:200],
        tags=["学习资料", file.file_type or "note"],
        remark=file.remark,
        source_image_url=file.file_url,
        ocr_summary=task.ocr_text[:500],
    )


def create_recognition_task(
    db: Session,
    current_user: User,
    payload: RecognitionStartRequest,
    *,
    retry_count: int = 0,
    batch_id: str = "",
    batch_order: int = 0,
) -> dict:
    file = get_file_or_404(db, payload.fileId, current_user)
    if batch_id and not file.batch_id:
        file.batch_id = batch_id
        file.batch_order = batch_order
    task_batch_id = file.batch_id or batch_id or ""
    task_batch_order = file.batch_order or batch_order or 0
    task = RecognitionTask(
        file_id=file.id,
        user_id=file.user_id,
        batch_id=task_batch_id,
        batch_order=task_batch_order,
        trace_id=uuid4().hex,
        status="pending",
        current_step=_stage_message("pending"),
        progress=0,
        retry_count=retry_count,
        pipeline_options_json=payload.model_dump(),
    )
    file.status = "processing"
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_out(task)


def _execute_recognition_pipeline(db: Session, task: RecognitionTask, payload: RecognitionStartRequest, *, raise_errors: bool = True) -> dict | None:
    file = db.get(UploadFile, task.file_id)
    if not file:
        message = "来源文件不存在"
        task.status = "failed"
        task.error_code = "IMAGE_READ_FAILED"
        task.error_stage = "preprocessing"
        task.error_message = message
        task.finished_at = now()
        db.commit()
        if raise_errors:
            raise AppException(message, code=404, http_status=404)
        return None

    try:
        image_path = file.original_path

        def preprocessing_stage():
            try:
                quality = assess_image_quality(file.original_path)
            except Exception as exc:
                raise PipelineError(f"图片读取或质量评估失败：{exc}", error_code="IMAGE_READ_FAILED", error_stage="preprocessing") from exc
            task.quality_json = quality
            if payload.enablePreprocess:
                processed = preprocess_image(file.original_path, db, task.id)
                file.processed_path = processed if processed != file.original_path else ""
                return processed
            create_model_log(
                db,
                task_id=task.id,
                model_type="opencv",
                model_name="opencv-preprocess-disabled",
                stage="preprocessing",
                output_summary="已跳过图像预处理",
                metadata={"quality": quality},
            )
            return file.original_path

        image_path = _run_stage(db, task, "preprocessing", 15, preprocessing_stage)

        yolo_result = {"mode": "off", "detections": [], "layoutType": "unknown", "quality": task.quality_json or {}}
        if payload.enableYOLO:
            yolo_image_path = file.original_path if settings.yolo_mode.lower() == "real" else image_path
            yolo_result = _run_stage(db, task, "yolo_running", 30, lambda: detect_layout(yolo_image_path, db, task.id))
        else:
            create_model_log(db, task_id=task.id, model_type="yolo", model_name="yolo-disabled", stage="yolo_running", output_summary="已跳过版面检测")
        yolo_result["quality"] = {**(yolo_result.get("quality") or {}), **(task.quality_json or {})}
        task.yolo_result = _dump(yolo_result)
        db.commit()

        ocr_result = {"rawText": "", "blocks": [], "formulaBlocks": []}
        if payload.enableOCR:
            def ocr_stage():
                start = perf_counter()
                result = run_ocr(image_path)
                cost = int((perf_counter() - start) * 1000)
                result["blocks"] = _normalize_blocks(result.get("blocks", []))
                result["formulaBlocks"] = _normalize_formula_blocks(result.get("formulaBlocks", []), "ocr")
                raw_text = str(result.get("rawText") or "")
                avg_conf = _avg_confidence(result["blocks"])
                status = "success"
                error_code = ""
                error_message = ""
                if not raw_text.strip() or not result["blocks"]:
                    status = "failed"
                    error_code = "OCR_EMPTY"
                    error_message = "OCR 未识别到有效文本"
                elif avg_conf < 0.45:
                    status = "failed"
                    error_code = "OCR_LOW_CONFIDENCE"
                    error_message = f"OCR 平均置信度偏低：{avg_conf:.2f}"
                create_model_log(
                    db,
                    task_id=task.id,
                    model_type="ocr",
                    model_name=get_ocr_model_name(),
                    stage="ocr_running",
                    error_code=error_code,
                    input_summary=image_path,
                    output_summary=f"识别文本块 {len(result.get('blocks', []))} 个，公式候选 {len(result.get('formulaBlocks', []))} 个",
                    metadata={"avgConfidence": round(avg_conf, 4)},
                    status=status,
                    cost_time=cost,
                    error_message=error_message,
                )
                if error_code and not payload.enableVLM:
                    raise PipelineError(error_message, error_code=error_code, error_stage="ocr_running")
                return result

            ocr_result = _run_stage(db, task, "ocr_running", 50, ocr_stage)
            task.ocr_text = ocr_result.get("rawText", "")
            task.ocr_blocks = _dump(ocr_result.get("blocks", []))
            task.ocr_formula_blocks = _dump(ocr_result.get("formulaBlocks", []))
            db.commit()

        merged = {"mergedBlocks": [], "mergedText": task.ocr_text}
        if payload.enableOCR:
            def formula_stage():
                detected = detect_formulas(
                    image_path,
                    ocr_blocks=ocr_result.get("blocks", []),
                    layout_context=yolo_result,
                    db=db,
                    task_id=task.id,
                )
                formulas = _dedupe_formula_blocks(_normalize_formula_blocks(ocr_result.get("formulaBlocks", []), "ocr") + _normalize_formula_blocks(detected, "formula"))
                return formulas, merge_text_and_formula_blocks(ocr_result.get("blocks", []), formulas)

            formula_blocks, merged = _run_stage(db, task, "formula_running", 65, formula_stage)
            task.ocr_formula_blocks = _dump(formula_blocks)
            db.commit()

        vlm_result = {"summary": "", "questions": []}
        normalized_result = {"summary": "", "questions": [], "validationWarnings": ["未启用 VLM"], "needsReview": True}
        if payload.enableVLM:
            def vlm_stage():
                start = perf_counter()
                context = {
                    "rawText": task.ocr_text,
                    "blocks": parse_json_list(task.ocr_blocks),
                    "formulaBlocks": parse_json_list(task.ocr_formula_blocks),
                    "mergedBlocks": merged.get("mergedBlocks", []),
                    "mergedText": merged.get("mergedText", task.ocr_text),
                    "quality": task.quality_json or {},
                }
                result = analyze_question(image_path, context, yolo_result)
                cost = int((perf_counter() - start) * 1000)
                questions = result.get("questions", []) if isinstance(result.get("questions"), list) else []
                if not result or not questions:
                    create_model_log(
                        db,
                        task_id=task.id,
                        model_type="vlm",
                        model_name=get_vlm_model_name(),
                        stage="vlm_running",
                        error_code="VLM_EMPTY_RESULT",
                        input_summary="图片 + OCR/公式/版面上下文",
                        output_summary="VLM 未返回可用题目",
                        status="failed",
                        cost_time=cost,
                    )
                    raise PipelineError("VLM 未返回可用题目", error_code="VLM_EMPTY_RESULT", error_stage="vlm_running")
                create_model_log(
                    db,
                    task_id=task.id,
                    model_type="vlm",
                    model_name=get_vlm_model_name(),
                    stage="vlm_running",
                    input_summary="图片 + OCR/公式/版面上下文",
                    output_summary=f"生成题目 {len(questions)} 道",
                    metadata={"provider": get_vlm_model_name()},
                    status="success",
                    cost_time=cost,
                )
                return result

            vlm_result = _run_stage(db, task, "vlm_running", 78, vlm_stage)
            task.vlm_summary = vlm_result.get("summary", "")
            task.vlm_result = _dump(vlm_result)
            db.commit()

            def parsing_stage():
                try:
                    return normalize_vlm_result(vlm_result, subject_hint=file.remark if file.remark else "", source_image_url=file.file_url)
                except Exception as exc:
                    raise PipelineError(f"VLM 结构校验失败：{exc}", error_code="VLM_INVALID_JSON", error_stage="parsing") from exc

            normalized_result = _run_stage(db, task, "parsing", 86, parsing_stage)
            task.normalized_result_json = normalized_result
            db.commit()

        def persisting_stage():
            created = []
            if normalized_result.get("questions"):
                created = _create_questions(db, task, file, normalized_result, vlm_result)
            if file.file_type == "note" or normalized_result.get("materialType") in {"note", "learning_material"}:
                _create_material(db, task, file, normalized_result)
            if payload.enableVLM and not created and file.file_type != "note":
                raise PipelineError("没有可写入的题目卡片", error_code="VLM_EMPTY_RESULT", error_stage="persisting")
            return created

        _run_stage(db, task, "persisting", 94, persisting_stage)

        task.status = "needs_review" if normalized_result.get("needsReview") else "completed"
        task.current_step = _stage_message(task.status)
        task.progress = 100
        task.finished_at = now()
        task.heartbeat_at = now()
        file.status = "recognized"
        db.commit()
        db.refresh(task)
        return task_out(task)
    except PipelineError as exc:
        _fail_task(db, task, file, error_code=exc.error_code, error_stage=exc.error_stage, message=str(exc))
        if raise_errors:
            raise AppException(f"识别任务执行失败：{exc}") from exc
        return None
    except Exception as exc:
        _fail_task(db, task, file, error_code="DB_WRITE_FAILED", error_stage="system", message=str(exc))
        if raise_errors:
            raise AppException(f"识别任务执行失败：{exc}") from exc
        return None


def run_recognition_task(task_id: int, payload_data: dict) -> None:
    with TASK_LOCK:
        db = SessionLocal()
        try:
            task = db.get(RecognitionTask, task_id)
            if not task or task.status != "pending":
                return
            task.started_at = now()
            task.heartbeat_at = task.started_at
            db.commit()
            _execute_recognition_pipeline(db, task, RecognitionStartRequest(**payload_data), raise_errors=False)
        finally:
            db.close()


def start_recognition(db: Session, current_user: User, payload: RecognitionStartRequest) -> dict:
    task_data = create_recognition_task(db, current_user, payload)
    task = db.get(RecognitionTask, task_data["id"])
    return _execute_recognition_pipeline(db, task, payload) or task_data


def batch_start_recognition(db: Session, current_user: User, payload: RecognitionBatchStartRequest) -> dict:
    files: list[UploadFile] = []
    failed: list[dict] = []
    for file_id in payload.fileIds:
        try:
            files.append(get_file_or_404(db, file_id, current_user))
        except Exception as exc:
            failed.append({"fileId": file_id, "message": str(exc)})
    existing_batch_id = next((item.batch_id for item in files if item.batch_id), "")
    batch_id = existing_batch_id or uuid4().hex
    tasks: list[dict] = []
    for index, file in enumerate(files, start=1):
        try:
            if not file.batch_id:
                file.batch_id = batch_id
                file.batch_order = index
            item = create_recognition_task(
                db,
                current_user,
                RecognitionStartRequest(
                    fileId=file.id,
                    enablePreprocess=payload.enablePreprocess,
                    enableYOLO=payload.enableYOLO,
                    enableOCR=payload.enableOCR,
                    enableVLM=payload.enableVLM,
                ),
                batch_id=batch_id,
                batch_order=file.batch_order or index,
            )
            tasks.append(item)
        except Exception as exc:
            failed.append({"fileId": file.id, "message": str(exc)})
    return {"batchId": batch_id, "tasks": tasks, "failed": failed, "successCount": len(tasks), "failedCount": len(failed)}


def list_tasks(
    db: Session,
    *,
    current_user: User,
    keyword: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
    all_users: bool = False,
) -> tuple[list[dict], int, int, int]:
    statement = select(RecognitionTask)
    if current_user.role != "admin" or not all_users:
        statement = statement.where(RecognitionTask.user_id == current_user.id)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.join(UploadFile).where(or_(UploadFile.file_name.like(like), RecognitionTask.current_step.like(like), RecognitionTask.error_code.like(like)))
    if status:
        statement = statement.where(RecognitionTask.status == status)
    if start_time:
        try:
            statement = statement.where(RecognitionTask.created_at >= datetime.strptime(start_time, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_time:
        try:
            statement = statement.where(RecognitionTask.created_at <= datetime.strptime(end_time, "%Y-%m-%d"))
        except ValueError:
            pass
    statement = statement.order_by(RecognitionTask.created_at.desc())
    rows, total, page, page_size = paginate(db, statement, page, page_size)
    return [task_out(row) for row in rows], total, page, page_size


def get_task_or_404(db: Session, task_id: int, current_user: User) -> RecognitionTask:
    task = db.get(RecognitionTask, task_id)
    if not task:
        raise AppException("识别任务不存在", code=404, http_status=404)
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise AppException("无权访问该识别任务", code=403, http_status=403)
    return task


def get_task(db: Session, task_id: int, current_user: User) -> dict:
    return task_out(get_task_or_404(db, task_id, current_user))


def retry_task(db: Session, task_id: int, current_user: User) -> dict:
    task = get_task_or_404(db, task_id, current_user)
    return {
        "retriedFrom": task.id,
        "task": start_recognition(db, current_user, RecognitionStartRequest(fileId=task.file_id)),
    }


def create_retry_task(db: Session, task_id: int, current_user: User) -> dict:
    task = get_task_or_404(db, task_id, current_user)
    payload = parse_json_dict(task.pipeline_options_json) or RecognitionStartRequest(fileId=task.file_id).model_dump()
    payload["fileId"] = task.file_id
    return {
        "retriedFrom": task.id,
        "task": create_recognition_task(db, current_user, RecognitionStartRequest(**payload), retry_count=task.retry_count + 1),
    }


def get_progress(db: Session, task_id: int, current_user: User) -> dict:
    task = get_task_or_404(db, task_id, current_user)
    return {
        "taskId": task.id,
        "status": task.status,
        "currentStep": task.current_step,
        "progress": task.progress,
        "message": task.current_step,
        "errorCode": task.error_code,
        "errorStage": task.error_stage,
        "qualityWarnings": parse_json_dict(task.quality_json).get("warnings", []),
    }


def get_batch(db: Session, batch_id: str, current_user: User) -> dict:
    if not batch_id:
        raise AppException("批次不存在", code=404, http_status=404)
    task_stmt = select(RecognitionTask).where(RecognitionTask.batch_id == batch_id).order_by(RecognitionTask.batch_order.asc(), RecognitionTask.id.asc())
    file_stmt = select(UploadFile).where(UploadFile.batch_id == batch_id).order_by(UploadFile.batch_order.asc(), UploadFile.id.asc())
    if current_user.role != "admin":
        task_stmt = task_stmt.where(RecognitionTask.user_id == current_user.id)
        file_stmt = file_stmt.where(UploadFile.user_id == current_user.id)
    tasks = db.scalars(task_stmt).all()
    files = db.scalars(file_stmt).all()
    if not tasks and not files:
        raise AppException("批次不存在", code=404, http_status=404)
    completed = [item for item in tasks if item.status == "completed"]
    needs_review = [item for item in tasks if item.status == "needs_review"]
    failed = [item for item in tasks if item.status == "failed"]
    running = [item for item in tasks if item.status not in TERMINAL_STATUSES]
    total = len(tasks)
    progress = int(sum(item.progress or 0 for item in tasks) / total) if total else 0
    status = "pending"
    if total and len(completed) + len(needs_review) + len(failed) == total:
        status = "failed" if len(failed) == total else "completed"
    elif running:
        status = "processing"
    question_total = db.scalar(select(func.count(Question.id)).where(Question.task_id.in_([item.id for item in tasks]))) if tasks else 0
    return {
        "batchId": batch_id,
        "status": status,
        "progress": progress,
        "total": total or len(files),
        "taskCount": total,
        "fileCount": len(files),
        "successCount": len(completed) + len(needs_review),
        "failedCount": len(failed),
        "runningCount": len(running),
        "questionCount": question_total or 0,
        "files": [file_out(item) for item in files],
        "tasks": [task_out(item) for item in tasks],
    }


def get_ocr_result(db: Session, task_id: int, current_user: User) -> dict:
    task = get_task_or_404(db, task_id, current_user)
    preprocess_url = ""
    if task.file and task.file.processed_path:
        preprocess_url = path_to_upload_url(task.file.processed_path)
    blocks = parse_json_list(task.ocr_blocks)
    formula_blocks = parse_json_list(task.ocr_formula_blocks)
    merged = merge_text_and_formula_blocks(blocks, formula_blocks)
    return {
        "rawText": task.ocr_text,
        "blocks": blocks,
        "formulaBlocks": formula_blocks,
        "mergedBlocks": merged["mergedBlocks"],
        "mergedText": merged["mergedText"],
        "quality": parse_json_dict(task.quality_json),
        "sections": build_ocr_sections(
            merged["mergedText"] or task.ocr_text,
            blocks,
            formula_blocks,
            parse_json_dict(task.yolo_result).get("detections", []),
        ),
        "layoutBlocks": parse_json_dict(task.yolo_result).get("detections", []),
        "yolo": parse_json_dict(task.yolo_result),
        "originalImageUrl": task.file.file_url if task.file else "",
        "preprocessImageUrl": preprocess_url,
    }


def get_vlm_result(db: Session, task_id: int, current_user: User) -> dict:
    task = get_task_or_404(db, task_id, current_user)
    stored = parse_json_dict(task.vlm_result)
    normalized = parse_json_dict(task.normalized_result_json)
    questions = db.scalars(select(Question).where(Question.task_id == task.id).order_by(Question.id.asc())).all()
    stored_questions = normalized.get("questions") or stored.get("questions", [])
    return {
        "summary": task.vlm_summary or normalized.get("summary", "") or stored.get("summary", ""),
        "layoutType": normalized.get("layoutType", stored.get("layoutType", "")),
        "materialType": normalized.get("materialType", stored.get("materialType", "")),
        "questions": _merge_stored_question_data(stored_questions if isinstance(stored_questions, list) else [], questions),
        "normalized": normalized,
        "needsReview": bool(normalized.get("needsReview")) or task.status == "needs_review",
        "validationWarnings": normalized.get("validationWarnings", []),
    }


def get_diagnostics(db: Session, task_id: int, current_user: User) -> dict:
    task = get_task_or_404(db, task_id, current_user)
    logs = db.scalars(select(ModelLog).where(ModelLog.task_id == task.id).order_by(ModelLog.created_at.asc())).all()
    stage_costs = {}
    for log in logs:
        key = log.stage or log.model_type
        if key:
            stage_costs[key] = stage_costs.get(key, 0) + (log.cost_time or 0)
    return {
        "task": task_out(task),
        "quality": parse_json_dict(task.quality_json),
        "errorCode": task.error_code,
        "errorStage": task.error_stage,
        "stageCosts": stage_costs,
        "logs": [
            {
                "id": log.id,
                "stage": log.stage,
                "modelType": log.model_type,
                "modelName": log.model_name,
                "status": log.status,
                "errorCode": log.error_code,
                "costTime": log.cost_time,
                "outputSummary": log.output_summary,
                "errorMessage": log.error_message,
            }
            for log in logs
        ],
    }
