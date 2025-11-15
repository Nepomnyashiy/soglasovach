from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Настройки базы данных
    DATABASE_URL: str = "postgresql+asyncpg://user:password@host:port/dbname"
    REDIS_URL: str = "redis://localhost:6379"

    # Секретный ключ для JWT. Очень важно, чтобы он был сложным и хранился в секрете.
    # В продакшене должен быть установлен через переменную окружения.
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_REPLACE_ME"
    ALGORITHM: str = "HS256"  # Алгоритм хеширования для JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Время жизни токена доступа в минутах

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
