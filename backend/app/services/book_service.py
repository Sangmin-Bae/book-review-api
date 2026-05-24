from sqlalchemy import select, text, func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate
from app.services.category_service import get_category


def get_book(db: Session, book_id: int) -> Book:
    """단건 조회 - 카테고리 정보 함께 로드제 (N+1 문제 방지)"""
    book = db.execute(
        select(Book).options(joinedload(Book.category)).where(Book.id == book_id)
    ).scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다")
    return book


def get_books(db: Session, skip: int = 0, limit: int = 100) -> list[Book]:
    """목록 조회 - 카테고리 정보 함께 로드 (N+1 문제 방지)"""
    return db.execute(
        select(Book).options(joinedload(Book.category)).offset(skip).limit(limit)
    ).scalars().all()


def create_book(db: Session, book_in: BookCreate) -> Book:
    """생성 - ISBN 중복 체크, 카테고리 존재 여부 검증"""
    if book_in.isbn:
        existing = db.execute(
            select(Book).where(Book.isbn == book_in.isbn)
        ).scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 ISBN입니다")

    if book_in.category_id:
        get_category(db, book_in.category_id)

    db_book = Book(**book_in.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, book_id: int, book_in: BookUpdate) -> Book:
    """수정 - 변경된 필드만 업데이트"""
    db_book = get_book(db, book_id)

    if book_in.category_id:
        get_category(db, book_in.category_id)  # 존재하지 않으면 404 자동 발생

    # exclude_none=True: None인 필드 제외 → 클라이언트가 보내지 않은 필드는 수정하지 않음
    update_data = book_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)

    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int) -> None:
    """삭제 - cascade 설정으로 관련 리뷰도 함께 삭제됨"""
    db_book = get_book(db, book_id)
    db.delete(db_book)
    db.commit()


def search_books_like(
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 100,
) -> list[Book]:
    """
    순수 LIKE 검색 방식 (성능 비교 기준점)

    동작:
        - WHERE title LIKE '%검색어%' 패턴으로 검색
        - 인덱스 스캔을 강제로 비활성화해서 순수 LIKE 전체 테이블 스캔
    특징:
        - 앞에 %가 붙으면 인덱스 사용 불가
        - pg_trgm GIN 인덱스가 있어도 사용하지 않음
        - 전체 테이블 순차 스캔(Sequential Scan) 강제
        - 데이터가 많을수록 선형으로 느려짐
        - SET LOCAL: 현재 트랜잭션에만 적용, 다른 요청에 영향 없음
    용도: trigram/FTS와의 성능 비교의 기준점(baseline)
    """
    # %검색어% 패턴: 검색어가 문자열 어디에든 포함되면 매칭
    search_pattern = f"%{query}%"

    # 현재 트랜잭션에서만 인덱스 스캔 비활성화
    # pg_trgm GIN 인덱스가 있어도 사용하지 않고 순차 스캔 강제
    db.execute(text("SET LOCAL enable_indexscan = off"))
    db.execute(text("SET LOCAL enable_bitmapscan = off"))

    result = db.execute(
        select(Book)
        .options(joinedload(Book.category))
        .where(
            # ilike: 대소문자 구분 없는 LIKE (case-insensitive)
            # 영어 검색 시 'Pachinko'와 'pachinko' 모두 매칭
            Book.title.ilike(search_pattern) |
            Book.author.ilike(search_pattern) |
            Book.description.ilike(search_pattern)
        )
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    # 인덱스 스캔 설정 복구
    db.execute(text("SET LOCAL enable_indexscan = on"))
    db.execute(text("SET LOCAL enable_bitmapscan = on"))

    return result


def search_books_trigram(
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 100,
) -> list[Book]:
    """
    pg_trgm(trigram) 검색 방식

    동작:
        - 텍스트를 3글자 조각으로 분리해서 GIN 인덱스로 검색
        - trigram 유사도 연산자(%)로 유사한 텍스트 검색
    특징:
        - LIKE '%검색어%' 패턴에서도 GIN 인덱스 활용 가능
        - 한국어 포함 모든 언어 지원 (언어 무관)
        - LIKE 검색보다 빠름
        - 유사도 기반 검색도 가능 (오타 허용)
        - title/author: GIN 인덱스 활용
        - description: 인덱스 없어서 ilike로 보완 (전체 스캔)
    용도: LIKE보다 빠르며 유사도 기반 검색이 필요할 때
    """
    search_pattern = f"%{query}%"

    return db.execute(
        select(Book)
        .options(joinedload(Book.category))
        .where(
            # % 연산자: trigram 유사도 비교
            # 영어 오타 허용 (pachingo -> pachinko)
            # 한국어는 음절 단위 분리로 유사도가 낮아 효과 제한적
            Book.title.op('%')(query) |
            Book.author.op('%')(query) |
            # description: GIN 인덱스 없음 -> ilike로 전체 스캔
            # 유사도 연산자를 description에도 적용하면
            # 인덱스 없이 전체 유사도 계산 -> 매우 느릴 수 있음
            Book.description.ilike(search_pattern)
        )
        .offset(skip)
        .limit(limit)
    ).scalars().all()


def search_books_fts(
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 100,
) -> list[Book]:
    """
    PostgreSQL FTS(Full-Text Search) 방식

    동작:
        - search_vector 컬럼의 GIN 인덱스를 활용해서 검색
        - 검색 결과를 관련도 점수 (ts_rank) 기준으로 정렬
    특징:
        - LIKE/trigram 보다 빠른 검색 (GIN 인덱스 + tsvector)
        - 가중치 기반 관련도 정렬 (제목 매칭 > 저자 매칭 > 설명 매칭)
        - 'simple' 토크나이저: 언어 무관, 공백/구두점 기준 토큰 분할
        - 형태소 분석 없음 (영어 어간 추출 미적용)
    용도: 검색 결과를 관련도 순으로 정렬해서 보여줄 때
    """
    # plainto_tsquery: 자연어 입력을 tsquery로 변환
    # to_tsquery와 달리 특수문자(&, |, !)가 포함된 입력도 오류 없이 처리
    ts_query = func.plainto_tsquery("simple", query)

    return db.execute(
        select(Book)
        .options(joinedload(Book.category))
        .where(
            # @@ 연산자: search_vector와 ts_query 토큰이 존재하면 매칭
            Book.search_vector.op("@@")(ts_query)
        )
        # ts_rank: 검색 결과의 관련도 점수 계산
        # search_vector의 가중치(A/B/C) 반영
        # desc(): 관련도 높은 순서로 정렬
        .order_by(func.ts_rank(Book.search_vector, ts_query).desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()