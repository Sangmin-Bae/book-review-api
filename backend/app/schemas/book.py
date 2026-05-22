from datetime import date
from pydantic import BaseModel, Field
from app.schemas.category import CategoryResponse


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    publisher: str | None = Field(default=None, max_length=100)
    description: str | None = None
    published_date: date | None = None
    isbn: str | None = Field(default=None, max_length=20)
    page_count: int | None = Field(default=None, ge=1)
    category_id: int | None = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    publisher: str | None = Field(default=None, max_length=100)
    description: str | None = None
    published_date: date | None = None
    isbn: str | None = Field(default=None, max_length=20)
    page_count: int | None = Field(default=None, ge=1)
    category_id: int | None = None


class BookResponse(BookBase):
    id: int
    category: CategoryResponse | None = None

    model_config = {"from_attributes": True}
