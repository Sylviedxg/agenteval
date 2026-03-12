from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://agenteval:agenteval123@localhost:5432/agenteval"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "agenteval-secret-key-change-in-production"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
