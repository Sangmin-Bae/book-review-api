from fastapi import FastAPI
from sqlalchemy import text
from app.core.config import settings
from app.db.session import SessionLocal

app = FastAPI(
    title="Book Review API",
    description="도서 검색 & 리뷰 API",
    version="0.1.0",
)


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
