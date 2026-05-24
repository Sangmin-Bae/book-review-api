"""add pg_trgm extension and trigram indexes

Revision ID: 491ed1307884
Revises: ee775d7498b9
Create Date: 2026-05-24 14:10:16.269620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '491ed1307884'
down_revision: Union[str, Sequence[str], None] = 'ee775d7498b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pg_trgm 확장 활성화
    # IF NOT EXISTS: 이미 설치된 경우 오류 없이 넘어감
    # pg_trgm이 있어야 GIN trigram 인덱스 생성 가능
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # title 컬럼에 GIN trigram 인덱스 추가
    # gin_trgm_ops: trigram 연산자 클래스 지정
    # 이 인덱스 덕분에 LIKE '%검색어%' 패턴에서도 인덱스 활용 가능
    op.create_index(
        "ix_books_title_trgm",
        "books",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"}
    )

    # author 컬럼에 GIN trigram 인덱스 추가
    op.create_index(
        "ix_books_author_trgm",
        "books",
        ["author"],
        postgresql_using="gin",
        postgresql_ops={"author": "gin_trgm_ops"}
    )


def downgrade() -> None:
    # 인덱스 제거
    op.drop_index("ix_books_author_trgm", table_name="books")
    op.drop_index("ix_books_title_trgm", table_name="books")

    # 확장 제거
    # 주의: 다른 테이블에서도 pg_trgm을 사용한다면 제거하면 안 됨
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
