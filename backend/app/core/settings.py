from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/studybuddy"
    OPENAI_API_KEY: str | None = None
    EMB_DIM: int = 256
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
