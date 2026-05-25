"""add search_tokens column and trigram index to books

Revision ID: 08b1e5cc9aae
Revises: c0a4d7a4d29a
Create Date: 2026-05-25 16:14:27.025606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08b1e5cc9aae'
down_revision: Union[str, Sequence[str], None] = 'c0a4d7a4d29a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # search_tokens 컬럼 추가
    # tokenize() 함수가 생성한 토큰 문자열을 저장
    # 예: "파친코 읽 소설 pachinko novel"
    op.add_column("books", sa.Column("search_tokens", sa.Text, nullable=True))

    # search_tokens 컬럼에 pg_trgm GIN 인덱스 추가
    # 토큰화된 문자열에 trigram 검색을 적용하기 위함
    # pg_trgm 확장은 이전 마이그레이션에서 이미 활성화했으므로 추가 필요 없음
    op.create_index(
        "ix_books_search_tokens_trgm",
        "books",
        ["search_tokens"],
        postgresql_using="gin",
        postgresql_ops={"search_tokens": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_books_search_tokens_trgm", table_name="books")
    op.drop_column("books", "search_tokens")
