from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate
from app.services.category_service import get_category


def get_book(db: Session, book_id: int) -> Book:
    """단건 조회 - 카테고리 정보 함께 로드"""
    book = db.execute(
        select(Book).options(joinedload(Book.category)).where(Book.id == book_id)
    ).scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다")
    return book


def get_books(db: Session, skip: int = 0, limit: int = 100) -> list[Book]:
    """목록 조회"""
    return db.execute(
        select(Book).options(joinedload(Book.category)).offset(skip).limit(limit)
    ).scalars().all()


def create_book(db: Session, book_in: BookCreate) -> Book:
    """생성 - ISBN 중복 체크, 카테고리 존재 여부 검증"""
    if book_in.isbn:
        existing = db.execute(
            select(Book).where(Book.isbn == book_in.isbn)
        ).scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 ISBN입니다")

    if book_in.category_id:
        get_category(db, book_in.category_id)

    db_book = Book(**book_in.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, book_id: int, book_in: BookUpdate) -> Book:
    """수정"""
    db_book = get_book(db, book_id)

    if book_in.category_id:
        get_category(db, book_in.category_id)

    update_data = book_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)

    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int) -> None:
    """삭제"""
    db_book = get_book(db, book_id)
    db.delete(db_book)
    db.commit()


def search_books_like(
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 100,
) -> list[Book]:
    """
    LIKE 검색 방식

    동작: WHERE title LIKE '%검색어%' 패턴으로 검색
    특징: 앞에 %가 붙으면 인덱스 사용 불가 -> 전체 테이블 스캔
    용도: 성능 비교의 기준점(baseline)
    """
    # %검색어% 패턴: 검색어가 문자열 어디에든 포함되면 매칭
    search_pattern = f"%{query}%"

    return db.execute(
        select(Book)
        .options(joinedload(Book.category))
        .where(
            # ilike: 대소문자 구분 없는 LIKE (case-insensitive)
            # 영어 검색 시 'Pachinko'와 'pachinko' 모두 매칭
            Book.title.ilike(search_pattern) |
            Book.author.ilike(search_pattern) |
            Book.description.ilike(search_pattern)
        )
        .offset(skip)
        .limit(limit)
    ).scalars().all()