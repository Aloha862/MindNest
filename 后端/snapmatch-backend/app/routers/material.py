from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.material import MaterialUpdateRequest
from app.services import material_service
from app.utils.response import page_data, success


router = APIRouter(prefix="/materials", tags=["学习资料管理模块"])


@router.get("/statistics")
def statistics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(material_service.statistics(db, current_user))


@router.get("")
def materials(
    keyword: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    startTime: str | None = None,
    endTime: str | None = None,
    page: int = 1,
    pageSize: int = Query(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows, total, page, page_size = material_service.list_materials(
        db,
        current_user=current_user,
        keyword=keyword,
        category=category,
        tag=tag,
        start_time=startTime,
        end_time=endTime,
        page=page,
        page_size=pageSize,
    )
    return success(page_data(rows, total, page, page_size))


@router.get("/{material_id}")
def detail(material_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(material_service.get_material(db, material_id, current_user))


@router.put("/{material_id}")
def update(material_id: int, payload: MaterialUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(material_service.update_material(db, material_id, current_user, payload))


@router.delete("/{material_id}")
def delete(material_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success(material_service.delete_material(db, material_id, current_user))
