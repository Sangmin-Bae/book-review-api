from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.db.session import get_db
from app.schemas.book import BookCreate, BookUpdate, BookResponse, BookCursorPage
from app.services import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookResponse])
def get_books(
        # 검색어 - None이면 전체 목록 반환
        q: str | None = Query(default=None, description="검색어 (제목/저자/설명)"),
        # 검색 방식 선택
        # like: 순수 LIKE 전체 스캔 (성능 기준점)
        # trigram: pg_trgm 유사도 검색 (GIN 인덱스 활용, 영어 오타 허용)
        search_type: Literal["like", "trigram", "fts", "token"] = Query(
            default="like",
            description="검색 방식: like(LIKE 순차 스캔), trigram(pg_trgm 유사도), fts(Full-Text Search), token(형태소 분석 + trigram)",
        ),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
):
    # 검색어가 없으면 전체 목록 반환
    if not q:
        return book_service.get_books(db, skip=skip, limit=limit)

    # 검색 방식에 따라 다른 함수 호출
    if search_type == "like":
        return book_service.search_books_like(db, q, skip=skip, limit=limit)
    elif search_type == "trigram":
        return book_service.search_books_trigram(db, q, skip=skip, limit=limit)
    elif search_type == "fts":
        return book_service.search_books_fts(db, q, skip=skip, limit=limit)
    elif search_type == "token":
        return book_service.search_books_token(db, q, skip=skip, limit=limit)

    return []


# Cursor 페이지네이션 전용 엔드포인트
# offset 방식(/books)과 별도로 분리 -  두 방식의 차이를 명확히 보여주기 위함
@router.get("/cursor", response_model=BookCursorPage)
def get_books_cursor(
        # 마지막으로 받은 도서의 id - 첫 페이지는 None
        cursor: int | None = Query(default=None, description="마지막으로 받은 도서 id (첫 페이지는 생략)"),
        # 한 페이지에 반환할 도서 수
        limit: int = Query(default=10, ge=1, le=100, description="페이지당 도서 수"),
        db: Session = Depends(get_db),
):
    return book_service.get_books_cursor(db, cursor=cursor, limit=limit)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
        book_id: int,
        db: Session = Depends(get_db),
):
    return book_service.get_book(db, book_id)


# status_code=201: 리소스 생성 성공 시 200 대신 201 반환 (HTTP 표준)
@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
        book_in: BookCreate,
        db: Session = Depends(get_db),
):
    return book_service.create_book(db, book_in)


@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
        book_id: int,
        book_in: BookUpdate,  # 변경할 필드만 포함 (PATCH 방식)
        db: Session = Depends(get_db),
):
    return book_service.update_book(db, book_id, book_in)


# status_code=204: 삭제 성공 시 응답 body 없음 (HTTP 표준)
@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
        book_id: int,
        db: Session = Depends(get_db),
):
    book_service.delete_book(db, book_id)
