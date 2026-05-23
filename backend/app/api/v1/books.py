from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from app.services import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookResponse])
def get_books(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
):
    return book_service.get_books(db, skip=skip, limit=limit)


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
