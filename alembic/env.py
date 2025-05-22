import os
from dotenv import load_dotenv
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# 1) load your .env so DATABASE_URL is available
load_dotenv()

# 2) Alembic config
config = context.config

# 3) override the INI’s blank URL with the env var
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL must be set in your environment")

config.set_main_option("sqlalchemy.url", database_url.replace("+asyncpg", ""))
# note: we'll pass sslmode via connect_args below

# 4) Logging
fileConfig(config.config_file_name)

# 5) Metadata
from app.database import Base

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    sync_url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
        connect_args={"sslmode": "require"},
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
