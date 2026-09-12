import os
from typing import List, Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart POS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-xerexlabs-smart-pos-development-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Individual DB Settings
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[str] = "5432"
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_DRIVER: Optional[str] = None

    # Database
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def model_post_init(self, __context):
        if not self.DATABASE_URL:
            env_db_url = os.getenv("DATABASE_URL")
            if env_db_url:
                self.DATABASE_URL = env_db_url
            elif self.DB_HOST:
                user = quote_plus(self.DB_USER or "")
                password = quote_plus(self.DB_PASSWORD or "")
                host = self.DB_HOST
                port = self.DB_PORT or "5432"
                name = self.DB_NAME or ""
                driver = self.DB_DRIVER or ("mysql+pymysql" if str(port) == "3306" else "postgresql")
                self.DATABASE_URL = f"{driver}://{user}:{password}@{host}:{port}/{name}"
            else:
                self.DATABASE_URL = "postgresql://postgres:postgreroot@localhost:5432/smart_pos"

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()

