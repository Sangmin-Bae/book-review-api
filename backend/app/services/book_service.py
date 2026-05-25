from sqlalchemy import select, text, func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.core.tokenizer import tokenize
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

    # 제목 + 저자 + 설명을 합쳐서 토크나이징
    # search_tokens에 저장해서 나중에 trigram 검색에 활용
    txt = f"{book_in.title} {book_in.author} {book_in.description or ''}"
    db_book.search_tokens = tokenize(txt)

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

    # 제목/저자/설명이 변경됐을 수 있으므로 토큰 재생성
    txt = f"{db_book.title} {db_book.author} {db_book.description or ''}"
    db_book.search_tokens = tokenize(txt)

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
    pg_trgm similarity 검색 방식

    동작:
        - % 연산자(similarity)로 title/author 유사도 비교
        - GIN trigram 인덱스 활용
    특징:
        - title/author: GIN trigram 인덱스 활용 + similarity 유사도 비교
        - 영어 오타 허용 (pachinka -> pachinko)
        - 한국어 바이트 구조 특성상 효과 제한적
        - description 제외 이유
            OR 조건에 인덱스 없는 컬럼이 포함되면
            전체 Seq Scan 으로 처리됨 (EXPLAIN ANALYZE 검증)
            description 검색은 token 방식(search_tokens)에서 담당
    용도: title/author 대상 영어 오타 허용 검색
    """
    return db.execute(
        select(Book)
        .options(joinedload(Book.category))
        .where(
            # % 연산자: trigram 유사도 비교
            # 영어 오타 허용 (pachingo -> pachinko)
            # 한국어는 음절 단위 분리로 유사도가 낮아 효과 제한적
            Book.title.op('%')(query) |
            Book.author.op('%')(query)
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


def search_books_token(
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 100,
) -> list[Book]:
    """
    Python 레벨 토크나이저 + word_similarity 검색 방식

    동작:
        - 검색어를 tokenize()로 형태소 분석
        - 분석된 토큰으로 search_tokens 컬럼에 word_similarity 검색
    특징:
        - 한국어 조사/어미 제거 후 검색 (FTS simple 토크나이저 한계 극복)
        - 영어 어간 추출 적용
        - word_similarity: search_tokens를 단어 단위로 분할 후
          각 단어와 검색어를 개별 비교해서 최고 유사도로 매칭 판단
          -> similarity와 달리 긴텍스트에서도 정확한 유사도 계산 가능
        - op('<%') or op('%>'): word_similarity 연산자
          검색어가 search_tokens의 어떤 단어와 유사하면 매칭
        - FTS와 달리 ts_rank 기반 관련도 정렬 없음
    용도: 한국어 + 영어 혼합 텍스트의 정확한 형태소 기반 검색
    """
    # 검색어도 동일한 토크나이저로 분석
    # 저장된 토큰과 같은 형태로 변환해야 매칭 가능
    tokenized_query = tokenize(query)

    if not tokenized_query:
        # 토크나이징 결과가 없으면 원본 검색어로 word_similarity fallback
        tokenized_query = query

    # word_similarity 임계값을 0.3으로 낮춰서 오타 허용 범위 확대
    # 기본값 0.6은 'pachinka' -> 'pachinko' 같은 오타도 통과 못할 . 있음
    # SET LOCAL: 현재 트랜잭션에만 적용, 다른 요청에 영향 없음
    db.execute(text("SET LOCAL pg_trgm.word_similarity_threshold = 0.3"))

    # word_similarity 유사도 검색
    # search_tokens에 저장된 토큰 문자열과 검색어 토큰을 word_similarity 방식으로 비교
    return db.execute(
        select(Book)
        .options(joinedload(Book.category))
        .where(
            # op('<%') or op('%>'): word_similarity 연산자
            # %> 연산자: 컬럼 %> 검색어
            # -> word_similarity(검색어, 컬럼) > threshold
            # -> search_tokens의 각 단어와 검색어를 개별 비교
            # -> 가장 유사한 단어의 유사도로 매칭 여부 결정
            # 예: tokenized_query = 'pachinka'
            #   search_tokens = 'pachinko 이진진 재일교포 소설'
            #   -> 'pachinka' vs 'pachinko' 단어 비교 -> 유사도 높음 -> 매칭
            # similarity와 달리 긴 텍스트에서도 단어 단위로 정확히 비교
            # func.word_similarity()가 아닌 연산자를 써야 GIN 인덱스 활용 가능
            Book.search_tokens.op('%>')(tokenized_query)
        )
        .offset(skip)
        .limit(limit)
    ).scalars().all()


def get_books_cursor(
        db: Session,
        cursor: int | None = None,
        limit: int = 10,
) -> dict:
    """
    Cursor 기반 페이지네이션 조회

    동작:
        - cursor(마지막으로 본 id)를 기준으로 다음 데이터 조회
        - cursor가 없으면 첫 페이지
        - limit + 1개를 조회해서 다음 페이지 존재 여부 확인
    특징:
        - id 기본키 인덱스 활용 -> 깊은 페이지도 일정한 속도
        - 데이터 추가/삭제 시에도 누락/중복 없음
        - offset 방식 대비 대용량 데이터에서 성능 우수
    """
    # limit + 1개를 조회하는 이유:
    # limit개만 조회하면 다음 페이지가 있는지 알 수 없음
    # 1개를 더 조회해서 limit개 초과 시 has_next=True로 판단
    query = (
        select(Book)
        .options(joinedload(Book.category))
        .order_by(Book.id.asc())  # id 오름차순 정렬 - cursor 기준점으로 사용
        .limit(limit + 1)
    )

    if cursor:
        # cursor가 있으면 해당 id 이후 데이터만 조회
        # WHERE id > cursor -> id 기본키 B-Tree 인덱스 활용
        query = query.where(Book.id > cursor)

    books = db.execute(query).scalars().all()

    # limit + 1개를 조회했으므로 limit개 초과 시 다음 페이지 존재
    has_next = len(books) > limit

    # has_next가 True이면 마지막 1개는 다음 페이지 확인용이므로 제거
    items = books[:limit]

    # 다음 cursor는 현재 페이지 마지막 항목의 id
    # has_next가 False면 다음 페이지 없으므로 None
    next_cursor = items[-1].id if has_next and items else None

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_next": has_next,
    }
