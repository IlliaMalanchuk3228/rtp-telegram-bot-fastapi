from databases import Database
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()

database = Database(settings.DATABASE_URL, min_size=1, max_size=3)
engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""), echo=True)

Base = declarative_base()
metadata = Base.metadata
