from datetime import date
from sqlalchemy import String, Text, ForeignKey, Date, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # FK - categories 테이블의 id를 참조
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    # Category와의 관계 정의
    category: Mapped["Category | None"] = relationship("Category", back_populates="books")

    # Review와의 관계 정의
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    # 검색 성능을 위한 인덱스
    # title, author는 검색에 자주 쓰이므로 인덱스 추가
    __table_args__ = (
        Index("ix_books_title", "title"),
        Index("ix_books_author", "author"),
    )

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title}>"
