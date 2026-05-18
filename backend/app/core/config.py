import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 애플리케이션
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # 데이터베이스
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = 5432
    postgres_db: str = "book_review"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
