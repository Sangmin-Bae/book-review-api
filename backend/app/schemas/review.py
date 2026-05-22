from datetime import datetime
from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    reviewer_name: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)


class ReviewCreate(ReviewBase):
    book_id: int


class ReviewUpdate(BaseModel):
    reviewer_name: str | None = Field(default=None, min_length=1, max_length=50)
    content: str | None = Field(default=None, min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)


class ReviewResponse(ReviewBase):
    id: int
    book_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}