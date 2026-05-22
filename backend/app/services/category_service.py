from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category(db: Session, category_id: int) -> Category:
    """단건 조회 - 없으면 404"""
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="카테코리를 찾을 수 없습니다")
    return category


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> list[Category]:
    """목록 조회"""
    # .scalars() - db.execute()로 반환된 result 객체를 ORM 객체로 변환
    # .all() - scalars()로 변환된 전체 ORM 객체를 리스트 반환 [obj, obj, ...]
    return db.execute(
        select(Category).offset(skip).limit(limit)
    ).scalars().all()


def create_category(db: Session, category_in: CategoryCreate) -> Category:
    """생성 - 이름 중복 체크"""
    existing = db.execute(
        select(Category).where(Category.name == category_in.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 카테고리 이름입니다")

    db_category = Category(**category_in.model_dump())  # model_dump() - pydantic 객체를 딕셔너리로 변환
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category_in: CategoryUpdate) -> Category:
    """수정 - 변경된 필드만 업데이트"""
    db_category = get_category(db, category_id)

    update_data = category_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> None:
    """삭"""
    db_category = get_category(db, category_id)
    db.delete(db_category)
    db.commit()
