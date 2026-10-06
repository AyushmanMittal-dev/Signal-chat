import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Signal Clone API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "signal-clone-secret-jwt-key-2026-super-secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./signal.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    FIXED_OTP: str = "123456"

settings = Settings()
