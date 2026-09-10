from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def normalize_page(page: int = 1, page_size: int = 10) -> tuple[int, int]:
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 10), 1), 100)
    return page, page_size


def paginate(db: Session, statement: Select, page: int = 1, page_size: int = 10) -> tuple[list, int, int, int]:
    page, page_size = normalize_page(page, page_size)
    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
    total = db.scalar(count_statement) or 0
    rows = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return rows, total, page, page_size
