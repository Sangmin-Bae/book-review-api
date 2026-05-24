from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


# 도서 카테고리 모델
# Book과 1:N 관계 (카테고리 하나에 여러 도서)
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Book과의 관계 정의
    # back_populates로 Book.category와 양뱡향 연결
    books: Mapped[list["Book"]] = relationship("Book", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name}>"
