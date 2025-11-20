import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead  # Импортируем UserRead для связей


# --- WorkflowTemplate Schemas ---
class WorkflowTemplateBase(BaseModel):
    name: str = Field(..., description="Название шаблона рабочего процесса")
    description: Optional[str] = Field(None, description="Описание шаблона")


class WorkflowTemplateCreate(WorkflowTemplateBase):
    pass


class WorkflowTemplateRead(WorkflowTemplateBase):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор шаблона")
    steps: List["WorkflowStepRead"] = [] # Forward reference

    class Config:
        orm_mode = True


# --- WorkflowStep Schemas ---
class WorkflowStepBase(BaseModel):
    name: str = Field(..., description="Название шага рабочего процесса")
    description: Optional[str] = Field(None, description="Описание шага")
    order: int = Field(..., ge=0, description="Порядковый номер шага в шаблоне")
    assignee_id: Optional[uuid.UUID] = Field(None, description="ID пользователя, ответственного за шаг")


class WorkflowStepCreate(WorkflowStepBase):
    pass


class WorkflowStepRead(WorkflowStepBase):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор шага")
    template_id: uuid.UUID = Field(..., description="ID шаблона, к которому относится шаг")
    assignee: Optional[UserRead] = None # Информация о назначенном пользователе

    class Config:
        orm_mode = True


# --- Attachment Schemas ---
class AttachmentBase(BaseModel):
    filename: str = Field(..., description="Имя файла")
    content_type: str = Field(..., description="Тип контента файла (MIME-тип)")


class AttachmentCreate(AttachmentBase):
    # s3_path будет генерироваться бэкендом после загрузки файла
    # instance_id и uploaded_by_id будут установлены при создании
    pass


class AttachmentRead(AttachmentBase):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор вложения")
    s3_path: str = Field(..., description="Путь к файлу в S3-совместимом хранилище (MinIO)")
    uploaded_at: datetime = Field(..., description="Дата и время загрузки файла")
    instance_id: uuid.UUID = Field(..., description="ID экземпляра рабочего процесса, к которому относится вложение")
    uploaded_by: UserRead # Кто загрузил файл

    class Config:
        orm_mode = True


# --- WorkflowInstance Schemas ---
class WorkflowInstanceBase(BaseModel):
    template_id: uuid.UUID = Field(..., description="ID шаблона рабочего процесса")
    # current_step_id будет установлен при создании, либо в процессе
    # status будет установлен при создании
    # created_by_id будет установлен на основе текущего пользователя


class WorkflowInstanceCreate(WorkflowInstanceBase):
    # При создании экземпляра можно опционально прикрепить существующие вложения
    attachment_ids: Optional[List[uuid.UUID]] = Field(None, description="Список ID вложений для прикрепления")


class WorkflowInstanceRead(WorkflowInstanceBase):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор экземпляра рабочего процесса")
    status: str = Field(..., description="Текущий статус экземпляра")
    current_step_id: Optional[uuid.UUID] = Field(None, description="ID текущего шага экземпляра")
    created_at: datetime = Field(..., description="Дата и время создания экземпляра")
    updated_at: datetime = Field(..., description="Дата и время последнего обновления экземпляра")

    template: WorkflowTemplateBase # Информация о шаблоне
    current_step: Optional["WorkflowStepRead"] = None # Forward reference
    created_by: UserRead # Кто создал экземпляр

    history: List["WorkflowHistoryRead"] = [] # Forward reference
    attachments: List[AttachmentRead] = []

    class Config:
        orm_mode = True


# --- WorkflowHistory Schemas ---
class WorkflowHistoryBase(BaseModel):
    action: str = Field(..., description="Выполненное действие (e.g., 'created', 'approved', 'rejected')")
    comment: Optional[str] = Field(None, description="Комментарий к действию")


class WorkflowHistoryCreate(WorkflowHistoryBase):
    # instance_id, step_id, user_id будут установлены бэкендом
    pass


class WorkflowHistoryRead(WorkflowHistoryBase):
    id: uuid.UUID = Field(..., description="Уникальный идентификатор записи истории")
    timestamp: datetime = Field(..., description="Дата и время выполнения действия")
    instance_id: uuid.UUID = Field(..., description="ID экземпляра рабочего процесса")
    step: WorkflowStepBase # Информация о шаге, на котором произошло действие
    user: UserRead # Кто выполнил действие

    class Config:
        orm_mode = True


# Update forward refs
WorkflowTemplateRead.update_forward_refs()
WorkflowStepRead.update_forward_refs()
WorkflowInstanceRead.update_forward_refs()
WorkflowHistoryRead.update_forward_refs()
