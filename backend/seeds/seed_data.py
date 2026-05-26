"""
Book Review API 테스트 데이터 생성 스크립트

실행 방법:
    docker compose exec backend python /app/seeds/seed_data.py
또는
    cd backend && python seeds/seed_data.py

사전 조건:
    - Docker 컨테이너 실행 중
    - alembic upgrade head 완료
소요 시간:
    - 약 35~40분 (300,000건 기준)
"""
import sys
import os
import random

# backend/ 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.book import Book
from app.models.category import Category
from app.core.tokenizer import tokenize

# 상수 정의
BATCH_SIZE = 1000  # 한 번에 INSERT할 건수

# 한국어 그룹 검색어 및 오타
KO_TARGET = "파친코"
KO_TYPOS = ["파칠코", "파칸코", "파찐코", "파치코", "파킨코"]

# 영어 그룹 검색어 및 오타
EN_TARGET = "pachinko"
EN_TYPOS = ["pachinka", "pachinco", "pachenko", "pachinke", "pachinck"]

# 혼합 그룹 검색어 및 오타
MX_TARGET_KO = "채식주의자"
MX_TARGET_EN = "vegetarian"
MX_TYPOS_KO = ["채식주이자", "채시주의자"]
MX_TYPOS_EN = ["vegeterian", "vegitarian"]

# 노이즈용 단어 목록
KO_NOISE_WORDS = [
    "소설", "역사", "과학", "철학", "시집", "에세이", "자서전",
    "경제", "정치", "문학", "예술", "음악", "영화", "스포츠",
    "여행", "요리", "건강", "교육", "심리", "사회", "문화",
]
KO_NOISE_AUTHORS = [
    "김영하", "이청준", "박경리", "황석영", "신경숙",
    "김훈", "공지영", "정유정", "김애란", "천명관",
]

EN_NOISE_WORDS = [
    "novel", "history", "science", "philosophy", "poetry", "essay",
    "biography", "economics", "politics", "literature", "art",
    "music", "film", "sports", "travel", "cooking", "health",
]
EN_NOISE_AUTHORS = [
    "Stephen King", "Haruki Murakami", "George Orwell",
    "Virginia Woolf", "Ernest Hemingway", "Franz Kafka",
    "Gabriel Garcia Marquez", "Toni Morrison", "Cormac McCarthy",
]

# 데이터 생성 함수
def make_book(title: str, author: str, description: str, category_id: int) -> Book:
    """Book 객체 생성 + search_tokens 자동 계산"""
    text = f"{title} {author} {description}"
    book = Book(
        title=title,
        author=author,
        description=description,
        category_id=category_id,
        search_tokens=tokenize(text),
    )
    return book


def generate_korean_books(category_id: int) -> list[Book]:
    """
    한국어 그룹 100,000건 생성

    구성:
        - 완전 일치 100건: title에 "파친코" 정확히 포함
        - 오타 100건: title에 오타 포함
        - 중간 매칭 1,000건: description에 "파친코" 포함
        - 비대상 98,800건: 관련 없는 한국어 데이터
    """
    books = []

    # 완전 일치 100건
    for i in range(100):
        books.append(make_book(
            title=f"파친코 {i + 1}",
            author=f"이민진 {i + 1}",
            description=f"재일교포 가족의 이야기를 담은 소설 {i + 1}",
            category_id=category_id,
        ))

    # 오타 100건
    for i in range(100):
        typo = KO_TYPOS[i % len(KO_TYPOS)]
        books.append(make_book(
            title=f"{typo} {i + 1}",
            author=f"이민진 {i + 1}",
            description=f"오타가 포함된 제목의 소설 {i + 1}",
            category_id=category_id,
        ))

    # 중간 매칭 1,000건 (description에 검색어 포함)
    for i in range(1000):
        word = random.choice(KO_NOISE_WORDS)
        books.append(make_book(
            title=f"한국 {word} 이야기 {i + 1}",
            author=random.choice(KO_NOISE_AUTHORS),
            description=f"소설 파친코를 소재로 한 {word} 관련 이야기 {i + 1}",
            category_id=category_id,
        ))

    # 비대상 98,800건
    for i in range(98800):
        word = KO_NOISE_WORDS[i % len(KO_NOISE_WORDS)]
        books.append(make_book(
            title=f"한국 {word} {i + 1}",
            author=random.choice(KO_NOISE_AUTHORS),
            description=f"한국의 {word}에 관한 이야기 {i + 1}",
            category_id=category_id,
        ))

    return books


def generate_english_books(category_id: int) -> list[Book]:
    """
    영어 그룹 100,000건 생성

    구성:
        - 완전 일치 100건: title에 "Pachinko" 정확히 포함
        - 오타 100건: title에 오타 포함
        - 중간 매칭 1,000건: description에 "pachinko" 포함
        - 비대상 98,800건: 관련 없는 영어 데이터
    """
    books = []

    # 완전 일치 100건
    for i in range(100):
        books.append(make_book(
            title=f"Pachinko Story {i + 1}",
            author=f"Min Jin Lee {i + 1}",
            description=f"An epic saga about pachinko culture {i + 1}",
            category_id=category_id,
        ))

    # 오타 100건
    for i in range(100):
        typo = EN_TYPOS[i % len(EN_TYPOS)]
        books.append(make_book(
            title=f"{typo.capitalize()} Story {i + 1}",
            author=f"Min Jin Lee {i + 1}",
            description=f"A story with typo in title {i + 1}",
            category_id=category_id,
        ))

    # 중간 매칭 1,000건 (description에 검색어 포함)
    for i in range(1000):
        word = random.choice(EN_NOISE_WORDS)
        books.append(make_book(
            title=f"English {word.capitalize()} {i + 1}",
            author=random.choice(EN_NOISE_AUTHORS),
            description=f"A novel {word} story involving pachinko culture {i + 1}",
            category_id=category_id,
        ))

    # 비대상 98,800건
    for i in range(98800):
        word = EN_NOISE_WORDS[i % len(EN_NOISE_WORDS)]
        books.append(make_book(
            title=f"English {word.capitalize()} {i + 1}",
            author=random.choice(EN_NOISE_AUTHORS),
            description=f"A story about {word} {i + 1}",
            category_id=category_id,
        ))

    return books


def generate_mixed_books(category_id: int) -> list[Book]:
    """
    혼합 그룹 100,000건 생성

    구성:
    - 완전 일치 100건: title에 "채식주의자 Vegetarian" 포함
    - 오타 100건: title에 한/영 오타 혼합
    - 중간 매칭 1,000건: description에 혼합 포함
    - 비대상 98,800건: 관련 없는 혼합 데이터
    """
    books = []

    # 완전 일치 100건
    for i in range(100):
        books.append(make_book(
            title=f"채식주의자 Vegetarian Story {i + 1}",
            author=f"한강 (Hangang) {i + 1}",
            description=f"채식을 선택한 여성의 이야기 a vegetarian story {i + 1}",
            category_id=category_id,
        ))

    # 오타 100건
    for i in range(100):
        ko_typo = MX_TYPOS_KO[i % len(MX_TYPOS_KO)]
        en_typo = MX_TYPOS_EN[i % len(MX_TYPOS_EN)]
        books.append(make_book(
            title=f"{ko_typo} {en_typo} {i + 1}",
            author=f"한강 (Hangang) {i + 1}",
            description=f"혼합 오타 mixed typo story {i + 1}",
            category_id=category_id,
        ))

    # 중간 매칭 1,000건
    for i in range(1000):
        ko_word = random.choice(KO_NOISE_WORDS)
        en_word = random.choice(EN_NOISE_WORDS)
        books.append(make_book(
            title=f"한국 {ko_word} Korean {en_word} {i + 1}",
            author=random.choice(KO_NOISE_AUTHORS),
            description=f"채식주의자를 다룬 vegetarian related {ko_word} {en_word} {i + 1}",
            category_id=category_id,
        ))

    # 비대상 98,800건
    for i in range(98800):
        ko_word = KO_NOISE_WORDS[i % len(KO_NOISE_WORDS)]
        en_word = EN_NOISE_WORDS[i % len(EN_NOISE_WORDS)]
        books.append(make_book(
            title=f"한국 {ko_word} Korean {en_word} {i + 1}",
            author=random.choice(EN_NOISE_AUTHORS),
            description=f"{ko_word} and {en_word} story {i + 1}",
            category_id=category_id,
        ))

    return books


# Batch INSERT
def batch_insert(db, books: list[Book], group_name: str) -> None:
    """
    1,000건 단위 배치 INSERT

    개별 INSERT 대신 배치로 처리해서 DB 왕복 횟수 최소화
    각 배치마다 commit 해서 메모리 사용량 조절
    """
    total = len(books)
    for i in range(0, total, BATCH_SIZE):
        batch = books[i:i + BATCH_SIZE]
        db.add_all(batch)
        db.commit()

        # 진행률
        done = min(i + BATCH_SIZE, total)
        print(f"[{group_name}] {done:,} / {total:,} 완료 ({done / total * 100:.1f}%)")


# 메인 실행
def main():
    db = SessionLocal()

    try:
        # 카테고리 조회 또는 생성
        category = db.execute(select(Category).where(Category.name == "테스트")).scalar_one_or_none()

        if not category:
            category = Category(name="테스트", description="성능 테스트용 카테고리")
            db.add(category)
            db.commit()
            db.refresh(category)

        print(f"카테고리 준비 완료: id={category.id}")
        print("=" * 60)

        # 한국어 그룹 생성 및 INSERT
        print("[1/3] 한국어 그룹 데이터 생성 중...")
        ko_books = generate_korean_books(category.id)
        print(f"[1/3] 한국어 그룹 {len(ko_books):,}건 INSERT 시작")
        batch_insert(db, ko_books, "한국어")

        # 영어 그룹 생성 및 INSERT
        print("[2/3] 영어 그룹 데이터 생성 중...")
        en_books = generate_english_books(category.id)
        print(f"[2/3] 영어 그룹 {len(en_books):,}건 INSERT 시작")
        batch_insert(db, en_books, "영어")

        # 혼합 그룹 생성 및 INSERT
        print("[3/3] 혼합 그룹 데이터 생성 중...")
        mx_books = generate_mixed_books(category.id)
        print(f"[3/3] 혼합 그룹 {len(mx_books):,}건 INSERT 시작")
        batch_insert(db, mx_books, "혼합")

        # 최종 확인
        total = db.execute(
            select(Book).where(Book.category_id == category.id)
        ).scalars()
        print("=" * 60)
        print(f"전체 INSERT 완료")

    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()