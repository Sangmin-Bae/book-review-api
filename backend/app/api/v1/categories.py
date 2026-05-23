from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services import category_service

# prefix: 이 라우터의 모든 엔드포인트 앞에 /categories가 붙음
# tags: Swagger UI에서 엔드포인트를 그룹으로 묶는 라벨
router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def get_categories(
        skip: int = 0,  # 건너뛸 항목 수 (페이지네이션)
        limit: int = 100,  # 최대 반환 항목 수
        db: Session = Depends(get_db),  # DB 세션 주입
):
    return category_service.get_categories(db, skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
        category_id: int,  # URL 경로에서 추출
        db: Session = Depends(get_db),
):
    return category_service.get_category(db, category_id)


# status_code=201: 리소스 생성 성공 시 200 대신 201 반환 (HTTP 표준)
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
        category_in: CategoryCreate,  # 요청 body → Pydantic이 자동 검증
        db: Session = Depends(get_db),
):
    return category_service.create_category(db, category_in)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
        category_id: int,
        category_in: CategoryUpdate,  # 변경할 필드만 포함 (PATCH 방식)
        db: Session = Depends(get_db),
):
    return category_service.update_category(db, category_id, category_in)


# status_code=204: 삭제 성공 시 응답 body 없음 (HTTP 표준)
# response_model 없음: body가 없으므로 스키마 불필요
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
):
    category_service.delete_category(db, category_id)
