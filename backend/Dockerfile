# 베이스 이미지
FROM python:3.11.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 후 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
