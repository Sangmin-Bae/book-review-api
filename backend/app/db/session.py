from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# DB 연결 엔진 생성
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,     # 세션 사용 전 연결이 살아있는지 확인
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,   # 명시적으로 commit()을 호출해야 DB에 반영됨
    autoflush=False,    # commit() 전에 자동으로 flush하지 않음
)

# SQLAlchemy 모델의 베이스 클래스
# 모든 모델은 이 Base를 상속받아 테이블로 인식됨
class Base(DeclarativeBase):
    pass

# FastAPI Dependency Injection용 세션 제공 함수
# yield로 세션을 제공하고 요청이 끝나면 자동으로 세션을 닫아줌
# 에러가 발생해도 finally 블록에서 반드시 세션이 닫힘
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
