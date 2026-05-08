import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    SMTP_EMAIL: str
    SMTP_PASSWORD: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_TLS: bool
    SMTP_SSL: bool
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_FULL_NAME: str = "Admin User"
    ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"

settings = Settings()
