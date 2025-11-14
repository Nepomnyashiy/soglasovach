from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """
    Получает пользователя по его ID.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        user_id (uuid.UUID): ID пользователя.

    Returns:
        Optional[User]: Объект пользователя или None, если не найден.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Получает пользователя по его электронной почте.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        email (str): Электронная почта пользователя.

    Returns:
        Optional[User]: Объект пользователя или None, если не найден.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Создает нового пользователя в базе данных.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        user (UserCreate): Схема Pydantic с данными для создания пользователя.

    Returns:
        User: Созданный объект пользователя.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,  # По умолчанию новый пользователь активен
        is_superuser=False, # По умолчанию не суперадмин
        is_verified=False # По умолчанию не верифицирован
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
