from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FAR API"
    VERSION: str = "1.0.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    DATABASE_URL: str = (
        "postgresql+asyncpg://far_user:far_password@127.0.0.1:5432/far_db"
    )


settings = Settings()
