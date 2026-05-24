from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.book_service import get_book


def get_review(db: Session, review_id: int) -> Review:
    """단건 조회적 - 없으면 404"""
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")
    return review


def get_reviews_by_book(db: Session, book_id: int, skip: int = 0, limit: int = 100) -> list[Review]:
    """특정 도서의 리뷰 목록 조회 - 도서 존재 여부 먼저 검증"""
    get_book(db, book_id)  # 존재하지 않으면 404 발생
    return db.execute(
        select(Review).where(Review.book_id == book_id).offset(skip).limit(limit)
    ).scalars().all()


def create_review(db: Session, review_in: ReviewCreate) -> Review:
    """생성 - 도서 존재 여부 검증"""
    get_book(db, review_in.book_id)  # 존재하지 않으면 404 자동 발생

    db_review = Review(**review_in.model_dump())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def update_review(db: Session, review_id: int, review_in: ReviewUpdate) -> Review:
    """수정 - 변경된 필드만 업데이트"""
    db_review = get_review(db, review_id)

    # exclude_none=True: None인 필드 제외 → 클라이언트가 보내지 않은 필드는 수정하지 않음
    update_data = review_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)

    db.commit()
    db.refresh(db_review)
    return db_review


def delete_review(db: Session, review_id: int) -> None:
    """삭제"""
    db_review = get_review(db, review_id)
    db.delete(db_review)
    db.commit()