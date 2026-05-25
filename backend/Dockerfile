# 베이스 이미지
FROM python:3.11.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 후 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NLTK 데이터 다운로드
# punkt: 단어/문장 분리에 필요한 언어 데이터
# 빌드 시 한 번만 다운받아서 이미지에 포함
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# 소스코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
