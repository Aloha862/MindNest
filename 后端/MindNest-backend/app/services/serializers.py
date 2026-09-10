import json

from app.models.model_log import ModelLog
from app.models.learning_material import LearningMaterial
from app.models.question import Question
from app.models.recognition_task import RecognitionTask
from app.models.subject import Subject
from app.models.upload_file import UploadFile
from app.models.user import User
from app.models.wrong_record import WrongRecord
from app.services.formula_service import merge_text_and_formula_blocks
from app.utils.file_utils import path_to_upload_url
from app.utils.time_utils import format_datetime


def parse_json_list(value: str | None) -> list:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def parse_json_dict(value: str | None) -> dict:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def user_info(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "role": user.role,
    }


def user_detail(user: User) -> dict:
    return {
        **user_info(user),
        "phone": user.phone,
        "status": user.status,
        "createdAt": format_datetime(user.created_at),
        "updatedAt": format_datetime(user.updated_at),
        "lastLoginTime": format_datetime(user.last_login_time),
    }


def file_out(file: UploadFile) -> dict:
    preprocess_url = ""
    if file.processed_path:
        try:
            preprocess_url = path_to_upload_url(file.processed_path)
        except Exception:
            preprocess_url = file.processed_path
    return {
        "id": file.id,
        "userId": file.user_id,
        "userName": file.user.nickname if file.user else "",
        "fileName": file.file_name,
        "fileType": file.file_type,
        "batchId": file.batch_id,
        "batchOrder": file.batch_order,
        "fileUrl": file.file_url,
        "originalImageUrl": file.file_url,
        "preprocessImageUrl": preprocess_url,
        "size": file.size,
        "status": file.status,
        "remark": file.remark,
        "createdAt": format_datetime(file.created_at),
        "updatedAt": format_datetime(file.updated_at),
    }


def task_out(task: RecognitionTask) -> dict:
    quality = parse_json_dict(task.quality_json)
    return {
        "id": task.id,
        "fileId": task.file_id,
        "fileName": task.file.file_name if task.file else "",
        "userId": task.user_id,
        "userName": task.user.nickname if task.user else "",
        "batchId": task.batch_id,
        "batchOrder": task.batch_order,
        "traceId": task.trace_id,
        "status": task.status,
        "currentStep": task.current_step,
        "progress": task.progress,
        "errorCode": task.error_code,
        "errorStage": task.error_stage,
        "retryCount": task.retry_count,
        "qualityWarnings": quality.get("warnings", []),
        "questionCount": len(task.questions or []),
        "ocrText": task.ocr_text,
        "vlmSummary": task.vlm_summary,
        "errorMessage": task.error_message,
        "createdAt": format_datetime(task.created_at),
        "updatedAt": format_datetime(task.updated_at),
        "startedAt": format_datetime(task.started_at),
        "heartbeatAt": format_datetime(task.heartbeat_at),
        "finishedAt": format_datetime(task.finished_at),
    }


def wrong_record_out(record: WrongRecord, include_question: bool = False) -> dict:
    attempts = sorted(record.attempts or [], key=lambda item: item.created_at or "", reverse=True)
    latest_attempt = attempts[0] if attempts else None
    return {
        "id": record.id,
        "questionId": record.question_id,
        "userId": record.user_id,
        "fileId": record.file_id,
        "taskId": record.task_id,
        "note": record.note,
        "masteryStatus": record.mastery_status,
        "reviewCount": record.review_count,
        "lastReviewTime": format_datetime(record.last_review_time),
        "attemptCount": len(attempts),
        "latestAttempt": attempt_out(latest_attempt) if latest_attempt else None,
        "source": record.source,
        "question": question_out(record.question) if include_question and record.question else None,
        "createdAt": format_datetime(record.created_at),
        "updatedAt": format_datetime(record.updated_at),
    }


def attempt_out(attempt) -> dict:
    if not attempt:
        return {}
    return {
        "id": attempt.id,
        "wrongRecordId": attempt.wrong_record_id,
        "questionId": attempt.question_id,
        "userId": attempt.user_id,
        "result": attempt.result,
        "selfRating": attempt.self_rating,
        "note": attempt.note,
        "createdAt": format_datetime(attempt.created_at),
    }


def question_out(question: Question, wrong_record: WrongRecord | None = None) -> dict:
    knowledge_points = parse_json_list(question.knowledge_points_json) or parse_json_list(question.knowledge_points)
    raw_vlm = parse_json_dict(question.raw_vlm_json)
    task = question.task
    ocr_blocks = parse_json_list(task.ocr_blocks) if task else []
    formula_blocks = parse_json_list(task.ocr_formula_blocks) if task else []
    merged = merge_text_and_formula_blocks(ocr_blocks, formula_blocks) if task else {"mergedBlocks": [], "mergedText": question.content}
    vlm_detail = {
        **raw_vlm,
        "answer": raw_vlm.get("answer", question.answer),
        "analysisSummary": raw_vlm.get("analysisSummary", question.analysis_summary),
        "formulas": raw_vlm.get("formulas", parse_json_list(question.formulas_json)),
    }
    return {
        "id": question.id,
        "taskId": question.task_id,
        "fileId": question.file_id,
        "userId": question.user_id,
        "title": question.title,
        "content": question.content,
        "subject": question.subject,
        "questionType": question.question_type,
        "knowledgePoints": knowledge_points,
        "options": parse_json_list(question.options_json),
        "formulas": parse_json_list(question.formulas_json),
        "rawVlmJson": raw_vlm,
        "vlmDetail": vlm_detail,
        "detailedAnalysis": raw_vlm.get("detailedAnalysis", ""),
        "solutionSteps": raw_vlm.get("solutionSteps", []),
        "commonMistakes": raw_vlm.get("commonMistakes", []),
        "errorCauseTags": raw_vlm.get("errorCauseTags", []),
        "reviewPlan": raw_vlm.get("reviewPlan", []),
        "similarPracticeSuggestions": raw_vlm.get("similarPracticeSuggestions", []),
        "estimatedTime": raw_vlm.get("estimatedTime", ""),
        "sourceBbox": parse_json_dict(question.source_bbox_json),
        "confidence": question.confidence,
        "reviewStatus": question.review_status,
        "difficulty": question.difficulty,
        "answer": question.answer,
        "analysisSummary": question.analysis_summary,
        "ocrText": task.ocr_text if task and task.ocr_text else question.content,
        "ocrBlocks": ocr_blocks,
        "formulaBlocks": formula_blocks,
        "mergedText": merged.get("mergedText") or (task.ocr_text if task else question.content),
        "mergedBlocks": merged.get("mergedBlocks", []),
        "qualityWarnings": parse_json_dict(task.quality_json).get("warnings", []) if task else [],
        "taskStatus": task.status if task else "",
        "fileName": question.file.file_name if question.file else "",
        "sourceImageUrl": question.source_image_url,
        "isWrong": wrong_record is not None,
        "wrongRecord": wrong_record_out(wrong_record) if wrong_record else None,
        "createdAt": format_datetime(question.created_at),
        "updatedAt": format_datetime(question.updated_at),
    }


def material_out(material: LearningMaterial) -> dict:
    return {
        "id": material.id,
        "fileId": material.file_id,
        "taskId": material.task_id,
        "userId": material.user_id,
        "title": material.title,
        "category": material.category,
        "summary": material.summary,
        "tags": parse_json_list(material.tags),
        "remark": material.remark,
        "sourceImageUrl": material.source_image_url,
        "ocrSummary": material.ocr_summary,
        "createdAt": format_datetime(material.created_at),
        "updatedAt": format_datetime(material.updated_at),
    }


def subject_out(subject: Subject) -> dict:
    return {
        "id": subject.id,
        "name": subject.name,
        "description": subject.description,
        "createdAt": format_datetime(subject.created_at),
    }


def log_out(log: ModelLog) -> dict:
    return {
        "id": log.id,
        "taskId": log.task_id,
        "modelType": log.model_type,
        "modelName": log.model_name,
        "stage": log.stage,
        "errorCode": log.error_code,
        "inputSummary": log.input_summary,
        "outputSummary": log.output_summary,
        "metadata": parse_json_dict(log.metadata_json),
        "status": log.status,
        "costTime": log.cost_time,
        "errorMessage": log.error_message,
        "createdAt": format_datetime(log.created_at),
    }
