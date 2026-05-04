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
    API_KEY: str = "233cc51050bb13ba5ac87110e1044b38379fbb3709f6c7955a16adb7f779eed3"


settings = Settings()
