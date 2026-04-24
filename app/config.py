from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    REDIS_URL: str = "redis://localhost:6379/0"
    OLLAMA_API_URL: str = "http://localhost:11434/v1/chat/completions"
    OLLAMA_MODEL: str = "llama3.2:3b"
    TELEGRAM_BOT_TOKEN: str | None = None
    ADMIN_TELEGRAM_ID: str | None = None
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
