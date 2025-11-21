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

    # Настройки MinIO
    MINIO_ENDPOINT: str = "localhost:9000"  # Или minio:9000 если из другого контейнера
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "soglasovach-bucket"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
