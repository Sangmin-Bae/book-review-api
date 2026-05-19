import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Backend 프로젝트 루트를 Python 경로에 추가
# alembic이 app 패키지를 찾을 수 있도록 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.session import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# alembic.ini 설정 로드
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# 로그 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# --autogenerate가 비교할 모델 메타데이터
# Base.metadata에 등록된 모든 모델을 감지
# 나중에 모델을 추가할 때마다 이 파일을 건드릴 필요 없이
# Base를 상속한 모델만 만들면 자동으로 감지됨
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    오프라인 모드: 실제 DB 연결 없이 SQL 파일만 생성
    실제 DB 접근 없이 마이그레이션 SQL을 미리 확인할 때 사용
    """
    # url = config.get_main_option("sqlalchemy.url")
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    온라인 모드: 실제 DB에 연결해서 마이그레이션 실행
    alembic upgrade head 실행 시 이 함수가 호출됨
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
