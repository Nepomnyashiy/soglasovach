from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.user import UserRead


# --- WorkflowTemplate Schemas ---
class WorkflowTemplateBase(BaseModel):
    name: str = Field(..., description="Название шаблона рабочего процесса")
    description: Optional[str] = Field(None, description="Описание шаблона")


class WorkflowTemplateCreate(WorkflowTemplateBase):
    pass


class WorkflowTemplateRead(WorkflowTemplateBase):
    id: int
    reference_id: Optional[str] = None
    steps: List["WorkflowStepRead"] = []

    model_config = ConfigDict(from_attributes=True)


# --- WorkflowStep Schemas ---
class WorkflowStepBase(BaseModel):
    name: str = Field(..., description="Название шага рабочего процесса")
    description: Optional[str] = Field(None, description="Описание шага")
    order: int = Field(..., ge=0, description="Порядковый номер шага в шаблоне")
    # `assignee_id` теперь int, так как ID пользователя в `User` - UUID.
    # Это нужно будет учесть при реализации ролей, а пока оставим так.
    # В реальном приложении здесь была бы ссылка на `role_id` (int).
    assignee_id: Optional[str] = Field(None, description="ID пользователя, ответственного за шаг")


class WorkflowStepCreate(WorkflowStepBase):
    pass


class WorkflowStepRead(WorkflowStepBase):
    id: int
    reference_id: Optional[str] = None
    template_id: int
    assignee: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)


# --- Attachment Schemas ---
class AttachmentBase(BaseModel):
    filename: str = Field(..., description="Имя файла")
    content_type: str = Field(..., description="Тип контента файла (MIME-тип)")


class AttachmentCreate(AttachmentBase):
    pass


class AttachmentRead(AttachmentBase):
    id: int
    reference_id: Optional[str] = None
    s3_path: str = Field(..., description="Путь к файлу в S3-совместимом хранилище (MinIO)")
    uploaded_at: datetime = Field(..., description="Дата и время загрузки файла")
    instance_id: Optional[int] = Field(None, description="ID экземпляра рабочего процесса, к которому относится вложение")
    uploaded_by: UserRead

    model_config = ConfigDict(from_attributes=True)


# --- WorkflowInstance Schemas ---
class WorkflowInstanceBase(BaseModel):
    template_id: int = Field(..., description="ID шаблона рабочего процесса")


class WorkflowInstanceCreate(WorkflowInstanceBase):
    attachment_ids: Optional[List[int]] = Field(None, description="Список ID вложений для прикрепления")


class WorkflowInstanceRead(WorkflowInstanceBase):
    id: int
    reference_id: Optional[str] = None
    status: str = Field(..., description="Текущий статус экземпляра")
    current_step_id: Optional[int] = Field(None, description="ID текущего шага экземпляра")
    created_at: datetime = Field(..., description="Дата и время создания экземпляра")
    updated_at: datetime = Field(..., description="Дата и время последнего обновления экземпляра")
    created_by: UserRead

    template: "WorkflowTemplateRead"
    current_step: Optional["WorkflowStepRead"] = None
    history: List["WorkflowHistoryRead"] = []
    attachments: List[AttachmentRead] = []

    model_config = ConfigDict(from_attributes=True)


# --- WorkflowHistory Schemas ---
class WorkflowHistoryBase(BaseModel):
    action: str = Field(..., description="Выполненное действие (e.g., 'created', 'approved', 'rejected')")
    comment: Optional[str] = Field(None, description="Комментарий к действию")


class WorkflowHistoryCreate(WorkflowHistoryBase):
    pass


class WorkflowHistoryRead(WorkflowHistoryBase):
    id: int
    timestamp: datetime = Field(..., description="Дата и время выполнения действия")
    instance_id: int
    step: "WorkflowStepRead"
    user: UserRead

    model_config = ConfigDict(from_attributes=True)


# Update forward refs
WorkflowTemplateRead.update_forward_refs()
WorkflowStepRead.update_forward_refs()
WorkflowInstanceRead.update_forward_refs()
WorkflowHistoryRead.update_forward_refs()
