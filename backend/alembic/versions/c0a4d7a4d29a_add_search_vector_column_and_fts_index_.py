"""add search_vector column and fts index to books

Revision ID: c0a4d7a4d29a
Revises: 491ed1307884
Create Date: 2026-05-24 17:52:39.523185

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


# revision identifiers, used by Alembic.
revision: str = 'c0a4d7a4d29a'
down_revision: Union[str, Sequence[str], None] = '491ed1307884'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # books 테이블에 tsvector 컬럼 추가
    # title + author + description을 합쳐서 검색 가능한 현태로 저장
    # nullable=True: 기존 데이터가 있을 수 있어서 초기엔 NULL 허용
    op.add_column(
        "books",
        sa.Column("search_vector", TSVECTOR, nullable=True),
    )

    # 기존 데이터의 search_vector 초기화
    # setweight: 컬럼별 가중치 부여
    # A(제목) > B(저자) > C(설명) 순으로 검색 관련도에 반영
    # coalesce: NULL이면 빈 문자열 대체 (NULL 오류 방지)
    # 'simple' 토크나이저:
    # 공백/구두점 기준으로 토큰을 분리하고 소문자로 변환
    # 언어별 처리(어간 추출, 불용어 제거) 없음
    # 한국어는 조사가 붙은 형태("파친코를")와 원형("파친코")이 다른 토큰으로 처리됨
    op.execute("""
        UPDATE books SET search_vector = 
            setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(author, '')), 'B') ||
            setweight(to_tsvector('simple', coalesce(description, '')), 'C')
    """)

    # search_vector 컬럼에 GIN 인덱스 추가
    # GIN(Generalized Inverted Index): tsvector 검색에 최적화된 인덱스
    # 역인덱스 구조라 특정 토큰을 포함하는 행을 빠르게 찾음
    op.create_index(
        "ix_books_search_vector",
        "books",
        ["search_vector"],
        postgresql_using="gin",
    )

    # INSERT/UPDATE 시 search_vector를 자동으로 갱신하는 트리거 함수 생성
    # 트리거가 없으면 도서 수정 시 search_vector를 앱 코드에서 직접 갱신해야 함
    op.execute("""
        CREATE OR REPLACE FUNCTION books_search_vector_update() RETURNS trigger AS $$
        BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
                    setweight(to_tsvector('simple', coalesce(NEW.author, '')), 'B') ||
                    setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'C');
                RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    # 트리거 등록
    # BEFORE INSERT OR UPDATE: 저장 전에 search_vector를 먼저 갱신
    # FOR EACH ROW: 변경된 행마다 개별 실행
    op.execute("""
        CREATE TRIGGER books_search_vector_trigger
        BEFORE INSERT OR UPDATE ON books
        FOR EACH ROW EXECUTE FUNCTION books_search_vector_update();
    """)


def downgrade() -> None:
    # 트리거 -> 함수 -> 인덱스 -> 컬럼 순서로 제거
    # 의존 관계가 있어서 역순으로 삭제해야 오류 없음
    op.execute("DROP TRIGGER IF EXISTS books_search_vector_trigger ON books")
    op.execute("DROP FUNCTION IF EXISTS books_search_vector_update")
    op.drop_index("ix_books_search_vector", table_name="books")
    op.drop_column("books", "search_vector")
