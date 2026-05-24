from datetime import date
from pydantic import BaseModel, Field
from app.schemas.category import CategoryResponse


# 도서 스키마
# Base: 공통 필드 / Create: 생성 요청 / Update: 수정 요청 / Response: 응답
class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)  # max_length는 DB 컬럼 길이와 일치
    author: str = Field(min_length=1, max_length=100)
    publisher: str | None = Field(default=None, max_length=100)
    description: str | None = None
    published_date: date | None = None
    isbn: str | None = Field(default=None, max_length=20)
    page_count: int | None = Field(default=None, ge=1)
    category_id: int | None = None


class BookCreate(BookBase):
    pass


# 수정 요청 — 모든 필드 선택적 (PATCH 방식: 변경할 필드만 전송)
# BookBase를 상속하지 않는 이유: Base의 필수 필드(title, author)를 선택적으로 바꿔야 하기 때문
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
    category: CategoryResponse | None = None  # 도서 조회 시 카테고리 정보 중첩 반환

    # ORM 객체를 Pydantic 스키마로 변환할 때 필요
    # SQLAlchemy 모델 객체의 속성을 직접 읽을 수 있게 허용
    model_config = {"from_attributes": True}
