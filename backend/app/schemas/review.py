from datetime import datetime
from pydantic import BaseModel, Field


# 리뷰 스키마
# Base: 공통 필드 / Create: 생성 요청 / Update: 수정 요청 / Response: 응답
class ReviewBase(BaseModel):
    reviewer_name: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)  # 1~5점 범위 제한


class ReviewCreate(ReviewBase):
    book_id: int  # Base가 아닌 Create에 위치 — 생성 시에만 필요한 필드


class ReviewUpdate(BaseModel):
    reviewer_name: str | None = Field(default=None, min_length=1, max_length=50)
    content: str | None = Field(default=None, min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)


class ReviewResponse(ReviewBase):
    id: int
    book_id: int
    created_at: datetime  # DB 서버가 자동 생성 — 요청에는 없고 응답에만 포함
    updated_at: datetime  # DB 서버가 자동 갱신 — 요청에는 없고 응답에만 포함

    # ORM 객체를 Pydantic 스키마로 변환할 때 필요
    # SQLAlchemy 모델 객체의 속성을 직접 읽을 수 있게 허용
    model_config = {"from_attributes": True}
