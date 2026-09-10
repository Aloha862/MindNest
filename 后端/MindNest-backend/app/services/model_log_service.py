from sqlalchemy.orm import Session

from app.models.model_log import ModelLog


def create_model_log(
    db: Session,
    *,
    task_id: int | None,
    model_type: str,
    model_name: str,
    stage: str = "",
    error_code: str = "",
    input_summary: str = "",
    output_summary: str = "",
    metadata: dict | None = None,
    status: str = "success",
    cost_time: int = 0,
    error_message: str = "",
) -> ModelLog:
    log = ModelLog(
        task_id=task_id,
        model_type=model_type,
        model_name=model_name,
        stage=stage,
        error_code=error_code,
        input_summary=input_summary,
        output_summary=output_summary,
        metadata_json=metadata or {},
        status=status,
        cost_time=cost_time,
        error_message=error_message,
    )
    db.add(log)
    db.flush()
    return log
