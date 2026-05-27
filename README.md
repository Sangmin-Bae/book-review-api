# Book Review API

> 백엔드 포트폴리오 프로젝트

FastAPI와 PostgreSQL로 구축한 도서 검색 및 리뷰 REST API입니다.
LIKE, pg_trgm similarity, Full-Text Search, Python 형태소 분석 + word_similarity 4가지 검색 방식을 직접 구현하고
300,000건 데이터 기준으로 EXPLAIN ANALYZE 성능을 비교했습니다.

---

## 기술 스택

|      분류      |              기술               |
|:--------------:|:-------------------------------:|
|    Backend     |            FastAPI              |
|    Database    |          PostgreSQL 16          |
|      ORM       |        SQLAlchemy 2.0           |
|   Migration    |            Alembic              |
|   Container    |         Docker Compose          |
| 한국어 형태소  |             Pecab               |
|  영어 어간 추출 |          NLTK PorterStemmer     |
| trigram 검색   |      PostgreSQL pg_trgm         |

---

## 개발 환경

|   분류   |    버전    |
|:--------:|:----------:|
|  Python  |  3.11.13   |

---

## 시스템 아키텍처

### 컨테이너 구성

```
┌─────────────────────────────────────┐
│           Docker Compose            │
│                                     │
│  ┌─────────────┐  ┌──────────────┐  │
│  │   backend   │  │      db      │  │
│  │  (FastAPI)  │◄─►│ (PostgreSQL) │  │
│  │   :8000     │  │    :5432     │  │
│  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────┘
```

### 애플리케이션 계층 구조

```
Request
   ↓
Router (app/api/v1/)
   ↓  경로 매핑, 요청/응답 스키마 검증
Service (app/services/)
   ↓  비즈니스 로직, DB 쿼리
Model (app/models/)
   ↓  SQLAlchemy ORM 모델
PostgreSQL
```

---

## 주요 기능

- **도서 CRUD** — 도서 생성/조회/수정/삭제, 카테고리 연결
- **카테고리 CRUD** — 도서 분류 관리
- **리뷰 CRUD** — 도서별 리뷰 작성/조회/수정/삭제
- **4가지 검색 방식** — LIKE, similarity, FTS, token (성능 비교 목적)
- **Cursor 페이지네이션** — offset 방식 대비 대용량 데이터 성능 우수

---

## 검색 성능 비교

### 테스트 환경

- **데이터**: 300,000건
  - 한국어 100,000건 (완전일치 100, 오타 100, 중간매칭 1,000, 비대상 98,800)
  - 영어 100,000건 (동일 구성, 검색어: pachinko)
  - 한/영 혼합 100,000건 (동일 구성, 검색어: 채식주의자/vegetarian)
- **DB**: PostgreSQL 16
- **측정 도구**: EXPLAIN ANALYZE

### 구현한 검색 방식

| 방식 | 설명 | 검색 대상 컬럼 |
|------|------|----------------|
| LIKE | 순수 LIKE 전체 스캔 (성능 기준점) | title, author, description |
| similarity | pg_trgm similarity 연산자(%) | title, author |
| FTS | PostgreSQL Full-Text Search (@@) | search_vector |
| token | Python 형태소 분석 + word_similarity(%>) | search_tokens |

> **similarity에서 description을 제외한 이유**
> OR 조건에 GIN 인덱스가 없는 컬럼(description)이 하나라도 포함되면
> PostgreSQL 플래너가 전체 Seq Scan을 선택합니다. EXPLAIN ANALYZE로 직접 검증했습니다.
> description 검색은 title + author + description을 모두 토큰화해서 저장하는 token 방식에서 담당합니다.

### 측정 방법

PostgreSQL `EXPLAIN ANALYZE`로 각 검색 방식의 실제 실행 계획과 소요 시간을 측정했습니다.

```sql
-- LIKE: 인덱스 강제 비활성화 후 순수 LIKE 스캔 측정
SET LOCAL enable_indexscan = off;
SET LOCAL enable_bitmapscan = off;
EXPLAIN ANALYZE
SELECT id, title, author FROM books
WHERE title ILIKE '%파친코%'
   OR author ILIKE '%파친코%'
   OR description ILIKE '%파친코%';

-- similarity: pg_trgm % 연산자, GIN trigram 인덱스 활용
EXPLAIN ANALYZE
SELECT id, title, author FROM books
WHERE title % '파친코'
   OR author % '파친코';

-- FTS: tsvector @@ tsquery, GIN 인덱스 활용
EXPLAIN ANALYZE
SELECT id, title, author FROM books
WHERE search_vector @@ plainto_tsquery('simple', '파친코');

-- token: word_similarity %> 연산자, GIN trigram 인덱스 활용
SET pg_trgm.word_similarity_threshold = 0.3;
EXPLAIN ANALYZE
SELECT id, title, author FROM books
WHERE search_tokens %> '파친코';
```

### 성능 측정 결과

#### 한국어 검색 ("파친코")

| 방식 | 스캔 방식 | 실행 시간 | 반환 행수 | 인덱스 |
|------|-----------|-----------|-----------|--------|
| LIKE | Parallel Seq Scan | 145.445 ms | 1,100 | 미사용 |
| similarity | Bitmap Index Scan | 0.603 ms | 100 | GIN trigram |
| FTS | Bitmap Index Scan | 0.149 ms | 100 | GIN |
| token | Bitmap Index Scan | 16.567 ms | 1,100 | GIN trigram |

#### 영어 검색 ("pachinko")

| 방식 | 스캔 방식 | 실행 시간 | 반환 행수 | 인덱스 |
|------|-----------|-----------|-----------|--------|
| LIKE | Parallel Seq Scan | 147.680 ms | 1,100 | 미사용 |
| similarity | Bitmap Index Scan | 2.004 ms | 145 | GIN trigram |
| FTS | Bitmap Index Scan | 0.973 ms | 1,100 | GIN |
| token | Bitmap Index Scan | 21.389 ms | 1,200 | GIN trigram |

#### 혼합 한국어 검색 ("채식주의자")

| 방식 | 스캔 방식 | 실행 시간 | 반환 행수 | 인덱스 |
|------|-----------|-----------|-----------|--------|
| LIKE | Parallel Seq Scan | 150.226 ms | 1,100 | 미사용 |
| similarity | Bitmap Index Scan | 2.953 ms | 0 | GIN trigram |
| FTS | Bitmap Index Scan | 0.373 ms | 100 | GIN |
| token | Bitmap Index Scan | 19.009 ms | 1,200 | GIN trigram |

#### 혼합 영어 검색 ("vegetarian")

| 방식 | 스캔 방식 | 실행 시간 | 반환 행수 | 인덱스 |
|------|-----------|-----------|-----------|--------|
| LIKE | Parallel Seq Scan | 148.550 ms | 1,100 | 미사용 |
| similarity | Bitmap Index Scan | 2.225 ms | 200 | GIN trigram |
| FTS | Bitmap Index Scan | 0.883 ms | 1,100 | GIN |
| token | Bitmap Index Scan | 21.660 ms | 1,200 | GIN trigram |

### 분석 및 결론

**LIKE**
- 항상 Parallel Seq Scan — 데이터가 늘수록 선형으로 느려짐
- 인덱스 강제 비활성화(`SET LOCAL enable_indexscan = off`) 후 측정한 순수 기준점

**similarity (pg_trgm)**
- title/author에 GIN trigram 인덱스 활용 → 0.6~3ms
- 영어 오타 허용: "pachinka" → "pachinko" 매칭 가능
- 한국어 "채식주의자": 한/영 혼합 title에서 전체 문자열 유사도 희석으로 0건 반환
  → similarity는 전체 문자열 대비 유사도를 계산하므로 긴 문자열에서 임계값 미달

**FTS (Full-Text Search)**
- 언어 무관하게 가장 안정적인 성능 (0.149~0.973ms)
- search_vector GIN 인덱스 활용
- 한국어 조사가 붙은 형태("파친코를")는 매칭 실패
  → PostgreSQL simple 토크나이저는 공백 기준 분리만 수행

**token (Python 형태소 분석 + word_similarity)**
- Pecab으로 한국어 형태소 분석, NLTK PorterStemmer로 영어 어간 추출
- 한국어 조사 처리: "파친코를" 검색 → "파친코" 매칭
- 영어 어간 추출: "novels" 검색 → "novel" 포함 도서 매칭
- word_similarity(%>) 연산자로 GIN trigram 인덱스 활용
  → func.word_similarity()는 모든 행에 함수 실행 후 비교(Seq Scan)
  → 연산자 방식이 인덱스 활용 가능
- FTS보다 느린 이유: Python 형태소 분석 + word_similarity 유사도 계산 두 단계 처리
- similarity "채식주의자" 0건 한계를 보완: 1,200건 정상 반환

### 한국어 검색 한계

- **similarity**: 한/영 혼합 컬럼에서 전체 문자열 유사도 희석
- **FTS simple 토크나이저**: 공백 기준 분리만 수행, 조사 처리 불가
- **token 방식**이 현재 구현에서 한국어 처리에 가장 적합
- 완전한 한국어 검색 품질이 필요하면 Elasticsearch (nori 플러그인) 도입 필요

---

## API 문서

서버 실행 후 아래 주소에서 Swagger UI를 확인할 수 있습니다.

```
http://localhost:8000/docs
```

### 엔드포인트 목록

#### 카테고리

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/v1/categories | 카테고리 목록 조회 |
| POST | /api/v1/categories | 카테고리 생성 |
| GET | /api/v1/categories/{category_id} | 카테고리 단건 조회 |
| PATCH | /api/v1/categories/{category_id} | 카테고리 수정 |
| DELETE | /api/v1/categories/{category_id} | 카테고리 삭제 |

#### 도서

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/v1/books | 도서 목록 조회 / 검색 |
| GET | /api/v1/books/cursor | Cursor 페이지네이션 조회 |
| POST | /api/v1/books | 도서 생성 |
| GET | /api/v1/books/{book_id} | 도서 단건 조회 |
| PATCH | /api/v1/books/{book_id} | 도서 수정 |
| DELETE | /api/v1/books/{book_id} | 도서 삭제 |

#### 리뷰

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/v1/books/{book_id}/reviews | 도서별 리뷰 목록 조회 |
| POST | /api/v1/books/{book_id}/reviews | 리뷰 생성 |
| PATCH | /api/v1/reviews/{review_id} | 리뷰 수정 |
| DELETE | /api/v1/reviews/{review_id} | 리뷰 삭제 |

---

## 프로젝트 구조

```
book-review-api/
├── backend/
│   ├── alembic/                  # 마이그레이션 관리
│   │   └── versions/             # 마이그레이션 파일
│   ├── app/
│   │   ├── api/v1/               # 라우터 (엔드포인트 정의)
│   │   │   ├── books.py
│   │   │   ├── categories.py
│   │   │   └── reviews.py
│   │   ├── core/
│   │   │   ├── config.py         # 환경변수 설정 (pydantic-settings)
│   │   │   └── tokenizer.py      # Python 형태소 분석기 (Pecab + NLTK)
│   │   ├── db/
│   │   │   └── session.py        # DB 연결 및 세션 관리
│   │   ├── models/               # SQLAlchemy ORM 모델
│   │   ├── schemas/              # Pydantic 요청/응답 스키마
│   │   ├── services/             # 비즈니스 로직
│   │   └── main.py               # FastAPI 앱 진입점
│   ├── seeds/
│   │   └── seed_data.py          # 성능 테스트용 300,000건 데이터 생성 스크립트
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── docker-compose.yml             # Production 환경
├── docker-compose.dev.yml.example # Development 환경 예시
├── .env.example
└── README.md
```

---

## 시작하기

### 사전 요구사항

- Docker, Docker Compose 설치

### 환경 설정

```bash
cp .env.example .env
# .env 파일에서 POSTGRES_USER, POSTGRES_PASSWORD 설정
```

### 실행

```bash
docker compose up
```

### 마이그레이션

```bash
docker compose exec backend alembic upgrade head
```

### 테스트 데이터 삽입

성능 측정을 위한 300,000건 데이터를 삽입합니다. 약 35~40분 소요됩니다.

```bash
docker compose exec backend python seeds/seed_data.py
```

### API 테스트

**Swagger UI** (권장)

브라우저에서 아래 주소로 접속하면 모든 엔드포인트를 직접 테스트할 수 있습니다.

```
http://localhost:8000/docs
```

**curl**

```bash
# 도서 검색 — FTS 방식 (기본값)
curl "http://localhost:8000/api/v1/books?q=파친코&search_type=fts"

# 도서 검색 — token 방식 (한국어 형태소 분석)
curl "http://localhost:8000/api/v1/books?q=파친코를&search_type=token"

# 도서 검색 — similarity 방식 (영어 오타 허용)
curl "http://localhost:8000/api/v1/books?q=pachinka&search_type=similarity"

# Cursor 페이지네이션 — 첫 페이지
curl "http://localhost:8000/api/v1/books/cursor?limit=10"

# Cursor 페이지네이션 — 다음 페이지
curl "http://localhost:8000/api/v1/books/cursor?cursor=10&limit=10"

# 헬스 체크
curl "http://localhost:8000/health"
```

---

## 기술적 의사결정

### 검색 방식 선택 — pg_trgm 한계 발견과 Python 토크나이저 도입

**문제**

pg_trgm trigram 검색이 한국어 환경에서 GIN 인덱스를 제대로 활용하지 못하는 문제를 발견했습니다. 한국어 음절이 UTF-8에서 3바이트를 차지해 trigram 조각 추출이 제한적이기 때문입니다. 또한 OR 조건에 GIN 인덱스가 없는 컬럼이 하나라도 포함되면 PostgreSQL 플래너가 전체 Seq Scan을 선택하는 동작을 EXPLAIN ANALYZE로 직접 검증했습니다.

**시도한 방법들**

- LIKE 검색: 전체 테이블 순차 스캔 → 데이터가 늘수록 선형으로 느려짐
- pg_trgm similarity: 한국어에서 GIN 인덱스 효과 제한적, 한/영 혼합 텍스트에서 유사도 희석
- PostgreSQL FTS: GIN 인덱스로 빠르지만 "파친코를" 같이 조사가 붙은 형태 검색 불가

**결론**

Python 레벨에서 형태소 분석을 수행하고 결과를 `search_tokens` 컬럼에 저장하는 방식 도입

- Pecab으로 한국어 조사/어미 제거 후 형태소 추출
- NLTK PorterStemmer로 영어 어간 추출
- word_similarity 연산자(`%>`)로 GIN trigram 인덱스 활용
- `func.word_similarity()` 대신 연산자를 사용한 이유: 함수 방식은 모든 행에 함수를 실행한 후 비교해 Seq Scan이 발생하지만, 연산자 방식은 GIN 인덱스 활용 가능

### Python 형태소 분석 라이브러리 선택

| 라이브러리 | 의존성 | 선택 |
|-----------|--------|------|
| KoNLPy | Java 런타임 필요 | ✗ |
| MeCab | C 라이브러리 필요 | ✗ |
| Pecab | 순수 Python | ✓ |

Docker 환경에서 외부 런타임 의존 없이 `pip install` 한 줄로 설치 가능한 Pecab을 선택했습니다.

### Cursor 페이지네이션 도입

offset 방식은 깊은 페이지일수록 이전 데이터를 모두 읽고 버리는 O(n) 비용이 발생합니다. Cursor 방식은 `WHERE id > cursor` 조건으로 기본키 B-Tree 인덱스를 활용해 항상 일정한 속도를 보장합니다. 단, 특정 페이지 번호로 직접 이동하는 기능은 구조적 한계로 현재 미지원이며 추후 개발할 예정입니다.

### word_similarity 방식이 similarity보다 긴 텍스트에 적합한 이유

similarity는 전체 문자열 대비 유사도를 계산해 `search_tokens`처럼 긴 텍스트에서 임계값을 넘기 어렵습니다. word_similarity는 텍스트를 단어 단위로 분할한 후 각 단어와 검색어를 개별 비교해 최고 유사도로 매칭을 판단합니다. "채식주의자" similarity 검색 0건 반환이 이 한계를 직접 보여줍니다.