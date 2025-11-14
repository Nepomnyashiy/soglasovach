from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings  # Будет создан позже


# Создаем асинхронный движок SQLAlchemy
# `pool_pre_ping=True` помогает поддерживать соединения активными
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Создаем фабрику сессий. `expire_on_commit=False` предотвращает
# истечение срока действия объектов после коммита, что удобно для асинхронной работы.
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI для получения асинхронной сессии базы данных.
    Создает сессию для каждого запроса и гарантирует ее закрытие.
    """
    async with AsyncSessionLocal() as session:
        yield session
