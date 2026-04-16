from logging.config import fileConfig

from sqlalchemy import pool, create_engine

from alembic import context

import sys
from pathlib import Path
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Добавляем путь к проекту, чтобы импортировать наши модели
sys.path.append(str(Path(__file__).parent.parent))

# Загружаем переменные окружения
load_dotenv()

from app.database import Base
from app.models import User, Log  # импортируем все модели, которые должны участвовать в миграциях

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
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

    """
    # Используем переменные окружения вместо alembic.ini
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    encoded_password = quote_plus(DB_PASSWORD)
    url = f"postgresql://{DB_USER}:{encoded_password}@localhost:5433/{DB_NAME}"

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

    """
    # Используем переменные окружения вместо alembic.ini
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    encoded_password = quote_plus(DB_PASSWORD)

    # Создаём СИНХРОННЫЙ engine для миграций
    engine = create_engine(
        f"postgresql://{DB_USER}:{encoded_password}@localhost:5433/{DB_NAME}",
        poolclass=pool.NullPool
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
