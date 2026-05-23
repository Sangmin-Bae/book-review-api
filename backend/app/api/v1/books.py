from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.db.session import get_db
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from app.services import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookResponse])
def get_books(
        # 검색어 - None이면 전체 목록 반환
        q: str | None = Query(default=None, description="검색어 (제목/저자/설명)"),
        # 검색 방식 - 지금은 like만 지원, 이후 trigram/fts 추가 예정
        search_type: Literal["like"] = Query(default="like", description="검색 방식: like(LIKE 검색)"),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
):
    # 검색어가 없으면 전체 목록 반환
    if not q:
        return book_service.get_books(db, skip=skip, limit=limit)

    # 검색 방식에 따라 다른 함수 호출
    # 이후 trigram, fts 추가 . 여기에 분기 추가
    if search_type == "like":
        return book_service.search_books_like(db, q, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
        book_id: int,
        db: Session = Depends(get_db),
):
    return book_service.get_book(db, book_id)


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
        book_in: BookCreate,
        db: Session = Depends(get_db),
):
    return book_service.create_book(db, book_in)


@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
        book_id: int,
        book_in: BookUpdate,
        db: Session = Depends(get_db),
):
    return book_service.update_book(db, book_id, book_in)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
        book_id: int,
        db: Session = Depends(get_db),
):
    book_service.delete_book(db, book_id)
