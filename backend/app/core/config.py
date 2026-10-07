import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Signal Clone API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "signal-clone-secret-jwt-key-2026-super-secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./signal.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    FIXED_OTP: str = os.getenv("FIXED_OTP", "123456")

settings = Settings()
