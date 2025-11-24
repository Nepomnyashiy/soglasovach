#!/bin/sh
set -e

# Активируем виртуальное окружение
# В Docker это не требуется, так как зависимости установлены глобально в контейнере
# . .venv/bin/activate

# Применяем миграции Alembic
echo "Applying database migrations..."
alembic upgrade head

# Запускаем Uvicorn сервер
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
