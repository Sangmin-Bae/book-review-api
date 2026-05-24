from pydantic import BaseModel, Field


# 카테고리 스키마
# Base: 공통 필드 / Create: 생성 요청 / Update: 수정 요청 / Response: 응답
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)  # max_length는 DB 컬럼 길이와 일치
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


# 수정 요청 - 모든 필드 선택적 (PATCH 방식: 변경할 필드만 전송)
# BookBase를 상속하지 않는 이유: Base의 필수 필드(name)를 선택적으로 바꿔야 하기 때문
class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class CategoryResponse(CategoryBase):
    id: int

    # ORM 객체를 Pydantic 스키마로 변환할 때 필요
    # SQLAlchemy 모델 객체의 속성을 직접 읽을 수 있게 허용
    model_config = {"from_attributes": True}
