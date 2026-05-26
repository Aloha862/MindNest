import json
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import AppException
from app.models.learning_material import LearningMaterial
from app.models.user import User
from app.schemas.material import MaterialUpdateRequest
from app.services.serializers import material_out
from app.utils.pagination import paginate


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def create_material(
    db: Session,
    *,
    user_id: int,
    file_id: int | None,
    task_id: int | None,
    title: str,
    category: str = "note",
    summary: str = "",
    tags: list[str] | None = None,
    remark: str = "",
    source_image_url: str = "",
    ocr_summary: str = "",
) -> LearningMaterial:
    material = LearningMaterial(
        user_id=user_id,
        file_id=file_id,
        task_id=task_id,
        title=title,
        category=category,
        summary=summary,
        tags=json.dumps(tags or [], ensure_ascii=False),
        remark=remark,
        source_image_url=source_image_url,
        ocr_summary=ocr_summary,
    )
    db.add(material)
    db.flush()
    return material


def list_materials(
    db: Session,
    *,
    current_user: User,
    keyword: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
    all_users: bool = False,
) -> tuple[list[dict], int, int, int]:
    statement = select(LearningMaterial)
    if current_user.role != "admin" or not all_users:
        statement = statement.where(LearningMaterial.user_id == current_user.id)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.where(or_(LearningMaterial.title.like(like), LearningMaterial.summary.like(like), LearningMaterial.remark.like(like)))
    if category:
        statement = statement.where(LearningMaterial.category == category)
    if tag:
        statement = statement.where(LearningMaterial.tags.like(f"%{tag}%"))
    start = _parse_time(start_time)
    end = _parse_time(end_time)
    if start:
        statement = statement.where(LearningMaterial.created_at >= start)
    if end:
        statement = statement.where(LearningMaterial.created_at <= end)
    statement = statement.order_by(LearningMaterial.created_at.desc())
    rows, total, page, page_size = paginate(db, statement, page, page_size)
    return [material_out(row) for row in rows], total, page, page_size


def get_material_or_404(db: Session, material_id: int, current_user: User) -> LearningMaterial:
    material = db.get(LearningMaterial, material_id)
    if not material:
        raise AppException("学习资料不存在", code=404, http_status=404)
    if current_user.role != "admin" and material.user_id != current_user.id:
        raise AppException("无权访问该学习资料", code=403, http_status=403)
    return material


def get_material(db: Session, material_id: int, current_user: User) -> dict:
    return material_out(get_material_or_404(db, material_id, current_user))


def update_material(db: Session, material_id: int, current_user: User, payload: MaterialUpdateRequest) -> dict:
    material = get_material_or_404(db, material_id, current_user)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "tags":
            value = json.dumps(value or [], ensure_ascii=False)
        setattr(material, key, value)
    db.commit()
    db.refresh(material)
    return material_out(material)


def delete_material(db: Session, material_id: int, current_user: User) -> dict:
    material = get_material_or_404(db, material_id, current_user)
    db.delete(material)
    db.commit()
    return {"id": material_id}


def statistics(db: Session, current_user: User, all_users: bool = False) -> dict:
    total_stmt = select(func.count(LearningMaterial.id))
    category_stmt = select(LearningMaterial.category, func.count(LearningMaterial.id)).group_by(LearningMaterial.category)
    if current_user.role != "admin" or not all_users:
        total_stmt = total_stmt.where(LearningMaterial.user_id == current_user.id)
        category_stmt = category_stmt.where(LearningMaterial.user_id == current_user.id)
    return {
        "total": db.scalar(total_stmt) or 0,
        "categoryDistribution": [{"name": name or "note", "value": count} for name, count in db.execute(category_stmt).all()],
    }
