from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.services import review_service

# prefix 없음 — 리뷰는 두 가지 URL 패턴을 가짐
# /books/{book_id}/reviews  → 생성/목록 조회
# /reviews/{review_id}      → 수정/삭제
router = APIRouter(tags=["reviews"])


# 특정 도서의 리뷰 목록 조회
# 중첩 리소스 구조: 리뷰는 항상 특정 도서에 속함
@router.get("/books/{book_id}/reviews", response_model=list[ReviewResponse])
def get_reviews(
        book_id: int,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
):
    return review_service.get_reviews_by_book(db, book_id, skip=skip, limit=limit)


# status_code=201: 리소스 생성 성공 시 200 대신 201 반환 (HTTP 표준)
@router.post("/books/{book_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
        book_id: int,
        review_in: ReviewCreate,
        db: Session = Depends(get_db),
):
    return review_service.create_review(db, review_in)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
        review_id: int,
        review_in: ReviewUpdate,  # 변경할 필드만 포함 (PATCH 방식)
        db: Session = Depends(get_db),
):
    return review_service.update_review(db, review_id, review_in)


# status_code=204: 삭제 성공 시 응답 body 없음 (HTTP 표준)
@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
        review_id: int,
        db: Session = Depends(get_db),
):
    review_service.delete_review(db, review_id)
