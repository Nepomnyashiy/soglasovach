from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import create_user, get_user_by_email
from app.schemas.user import UserCreate, UserRead
from app.db.session import get_async_session

# Создаем роутер для пользовательских эндпоинтов
router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Регистрирует нового пользователя в системе.

    Args:
        user_in (UserCreate): Данные для создания пользователя (email, пароль).
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        UserRead: Созданный пользователь без конфиденциальных данных.

    Raises:
        HTTPException: Если пользователь с таким email уже существует.
    """
    # Проверяем, существует ли пользователь с таким email
    existing_user = await get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован."
        )

    # Создаем нового пользователя
    user = await create_user(db, user_in)
    return user
