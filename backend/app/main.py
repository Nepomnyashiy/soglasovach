from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager # NEW

from app.db.session import get_async_session
from app.api.endpoints import users, auth, workflow # Импортируем наши новые роутеры
from app.core.minio_client import minio_client # NEW


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполнится при старте приложения
    print("Приложение запускается...")
    await minio_client.ensure_bucket_exists()
    print("Бакет в MinIO проверен и готов к работе.")
    yield
    # Код, который выполнится при остановке приложения
    print("Приложение останавливается...")


app = FastAPI(
    title="Soglasovach API",
    description="API для сервиса автоматизации корпоративных рабочих процессов.",
    version="0.1.0",
    lifespan=lifespan # NEW
)

# Включаем роутеры в основное приложение
app.include_router(users.router, prefix="/users", tags=["Пользователи"])
app.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
app.include_router(workflow.router, prefix="/workflow", tags=["Рабочие процессы"]) # Добавил роутер рабочих процессов


@app.get("/")
async def read_root():
    """Простой корневой эндпоинт для подтверждения работы API."""
    return {"status": "ok", "message": "Добро пожаловать в Soglasovach API!"}


@app.get("/test-db")
async def test_db_connection(db: AsyncSession = Depends(get_async_session)):
    """
    Тестовый эндпоинт для проверки подключения к базе данных.
    """
    try:
        # Выполняем простой запрос для проверки соединения
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Подключение к базе данных успешно!"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка подключения к базе данных: {e}"}



