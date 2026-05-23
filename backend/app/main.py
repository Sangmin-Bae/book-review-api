from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from app.api.v1 import categories, books, reviews

app = FastAPI(
    title="Book Review API",
    description="도서 검색 & 리뷰 API",
    version="0.1.0",
)

# 라우터 등록
# prefix="/api/v1" + 각 라우터의 prefix가 합쳐져서 최종 URL 결정
# 예) /api/v1 + /categories = /api/v1/categories
app.include_router(categories.router, prefix="/api/v1")
app.include_router(books.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    # DB 연결 상태 확인
    db_status = "ok"

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "env": settings.app_env,
        "db_host": settings.postgres_host,
        "db_status": db_status,
    }
