import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Общие поля, которые есть у всех схем User
class UserBase(BaseModel):
    email: EmailStr = Field(default=..., example="user@example.com", description="Электронная почта пользователя")


# Схема для создания нового пользователя (при регистрации)
# Наследует email от UserBase и добавляет пароль
class UserCreate(UserBase):
    password: str = Field(default=..., min_length=8, example="Str0ngPa$$w0rd", description="Пароль пользователя")


# Схема для обновления пользователя
# Все поля опциональные
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(default=None, example="user@example.com", description="Новая электронная почта")
    password: Optional[str] = Field(default=None, min_length=8, example="Str0ngPa$$w0rd", description="Новый пароль")


# Схема для чтения данных пользователя из API
# Не содержит пароль и другие служебные поля
class UserRead(UserBase):
    id: uuid.UUID = Field(default=..., example="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", description="Уникальный идентификатор")
    is_active: bool = Field(default=..., example=True, description="Активен ли пользователь")
    is_superuser: bool = Field(default=..., example=False, description="Является ли пользователь суперадмином")
    is_verified: bool = Field(default=..., example=False, description="Подтвердил ли пользователь свою почту")

    model_config = ConfigDict(from_attributes=True)


# Схема, представляющая пользователя как объект в базе данных
# Включает хешированный пароль, никогда не должна возвращаться через API
class UserInDB(UserRead):
    hashed_password: str
