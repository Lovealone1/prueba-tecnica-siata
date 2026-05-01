from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: SecretStr

    APP_NAME: str = "Prueba Tecnica SIATA"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: str = "*"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_KEY_PREFIX: str = "app"
    REDIS_TTL_SECONDS: int = 3600
    REDIS_ENABLED: bool = True

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    JWT_SECRET: str = "super_secret_jwt_key_please_change"
    JWT_EXPIRES_IN_MINUTES: int = 10080  # 1 week in minutes

    @property
    def APP_ENV(self) -> str:
        return self.ENVIRONMENT

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return ["*"] if self.CORS_ORIGINS.strip() == "*" else [
            o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
