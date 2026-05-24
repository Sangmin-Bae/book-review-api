from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


# 도서 리뷰 모델
# Book과 N:1 관계 (리뷰는 반드시 특정 도서에 속함)
class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reviewer_name: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1~5점

    # server_default=func.now(): DB 서버 시간 기준으로 자동 기록
    # 앱 서버 시간이 아닌 DB 시간 기준이라 여러 서버 환경에서도 일관성 보장
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # onupdate=func.now(): UPDATE 시 자동으로 현재 시간으로 갱신
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # FK - books 테이블의 id를 참조
    # ondelete="CASCADE": 도서 삭제 시 해당 도서의 리뷰도 함께 삭제
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Book과의 관계 정의
    # back_populates로 Book.reviews와 양방향 연결
    book: Mapped["Book"] = relationship("Book", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review id={self.id} book_id={self.book_id} rating={self.rating}>"
