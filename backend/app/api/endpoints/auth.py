from datetime import datetime, timedelta, timezone
from typing import Annotated
import uuid # Импортируем модуль uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.crud.user import get_user_by_email, get_user
from app.schemas.token import Token, TokenData
from app.schemas.user import UserRead
from app.db.session import get_async_session
from app.models.user import User


# Создаем роутер для аутентификации
router = APIRouter()

# Схема OAuth2 для получения токена.
# "tokenUrl" указывает, куда клиент должен отправить учетные данные для получения токена.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Создает JWT токен доступа.

    Args:
        data (dict): Данные, которые будут закодированы в токен (например, ID пользователя).
        expires_delta (timedelta | None): Время жизни токена. Если None, используется значение по умолчанию из настроек.

    Returns:
        str: Закодированный JWT токен.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Зависимость FastAPI для получения текущего аутентифицированного пользователя.
    Декодирует и проверяет JWT токен.

    Args:
        token (str): JWT токен из заголовка Authorization.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        User: Объект текущего пользователя.

    Raises:
        HTTPException: Если токен недействителен или пользователь не найден.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = await get_user(db, uuid.UUID(token_data.user_id))
    if user is None:
        raise credentials_exception
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_async_session)
):
    """
    Эндпоинт для получения JWT токена доступа.

    Args:
        form_data (OAuth2PasswordRequestForm): Данные формы (username, password).
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        Token: Объект токена доступа.

    Raises:
        HTTPException: Если учетные данные недействительны.
    """
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Эндпоинт для получения информации о текущем аутентифицированном пользователе.

    Args:
        current_user (User): Текущий аутентифицированный пользователь (предоставляется зависимостью).

    Returns:
        UserRead: Информация о текущем пользователе.
    """
    return current_user
