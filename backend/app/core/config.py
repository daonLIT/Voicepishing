from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    APP_ENV: str = "dev"
    MAX_TURNS: int = 6
    CONCURRENCY: int = 10
    USE_STUB_LLM: bool = True
    class Config: env_file = ".env"

settings = Settings()
