from minio import Minio
from minio.error import S3Error
from app.core.config import settings
from fastapi import UploadFile
import uuid
import logging

logger = logging.getLogger(__name__)

class MinioClient:
    """
    Класс-клиент для взаимодействия с MinIO.
    """
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False # Используйте True, если ваш MinIO настроен с SSL/TLS
        )
        self.bucket_name = settings.MINIO_BUCKET

    async def ensure_bucket_exists(self):
        """
        Проверяет существование бакета и создает его, если он не существует.
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"MinIO bucket '{self.bucket_name}' created successfully.")
            else:
                logger.info(f"MinIO bucket '{self.bucket_name}' already exists.")
        except S3Error as e:
            logger.error(f"Error ensuring MinIO bucket exists: {e}")
            raise

    async def upload_file(self, file: UploadFile) -> str:
        """
        Загружает файл в MinIO.

        Args:
            file (UploadFile): Файл для загрузки из FastAPI.

        Returns:
            str: Путь к файлу в MinIO (объектное имя).
        """
        object_name = f"{uuid.uuid4()}/{file.filename}"
        try:
            # Читаем содержимое файла асинхронно
            contents = await file.read()
            self.client.put_object(
                self.bucket_name,
                object_name,
                data=bytes(contents),
                length=len(contents),
                content_type=file.content_type
            )
            logger.info(f"File '{file.filename}' uploaded to MinIO as '{object_name}'.")
            return object_name
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise
        finally:
            # Важно закрыть файл
            await file.close()

    async def download_file(self, object_name: str) -> bytes:
        """
        Скачивает файл из MinIO.

        Args:
            object_name (str): Путь к файлу в MinIO (объектное имя).

        Returns:
            bytes: Содержимое файла.
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            file_content = response.read()
            logger.info(f"File '{object_name}' downloaded from MinIO.")
            return file_content
        except S3Error as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            raise
        finally:
            response.close()
            response.release_conn()

# Инициализация клиента MinIO
minio_client = MinioClient()
