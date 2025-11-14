from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(..., description="Токен доступа JWT")
    token_type: str = Field("bearer", description="Тип токена")


class TokenData(BaseModel):
    user_id: str | None = Field(None, description="ID пользователя (subject)")
