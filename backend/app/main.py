from fastapi import FastAPI

app = FastAPI(
    title="Book Review API",
    description="도서 검색 & 리뷰 API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
