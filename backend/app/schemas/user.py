import uuid
from pydantic import BaseModel, EmailStr, Field


# Общие поля, которые есть у всех схем User
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com", description="Электронная почта пользователя")


# Схема для создания нового пользователя (при регистрации)
# Наследует email от UserBase и добавляет пароль
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="Str0ngPa$$w0rd", description="Пароль пользователя")


# Схема для обновления пользователя
# Все поля опциональные
class UserUpdate(UserBase):
    email: EmailStr | None = Field(None, example="user@example.com", description="Новая электронная почта")
    password: str | None = Field(None, min_length=8, example="Str0ngPa$$w0rd", description="Новый пароль")


# Схема для чтения данных пользователя из API
# Не содержит пароль и другие служебные поля
class UserRead(UserBase):
    id: uuid.UUID = Field(..., example="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", description="Уникальный идентификатор")
    is_active: bool = Field(..., example=True, description="Активен ли пользователь")
    is_superuser: bool = Field(..., example=False, description="Является ли пользователь суперадмином")
    is_verified: bool = Field(..., example=False, description="Подтвердил ли пользователь свою почту")

    class Config:
        orm_mode = True


# Схема, представляющая пользователя как объект в базе данных
# Включает хешированный пароль, никогда не должна возвращаться через API
class UserInDB(UserRead):
    hashed_password: str
