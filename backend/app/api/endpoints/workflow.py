from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.db.session import get_async_session
from app.api.endpoints.auth import get_current_user
from app.schemas.user import UserRead
from app.schemas.workflow import (
    WorkflowTemplateCreate,
    WorkflowTemplateRead,
    WorkflowStepCreate,
    WorkflowStepRead,
    WorkflowInstanceCreate,
    WorkflowInstanceRead,
    AttachmentRead,
    AttachmentCreate,
)
from app.crud import workflow as crud_workflow
from app.models.workflow import WorkflowTemplate, WorkflowInstance, WorkflowStep, Attachment
from app.core.minio_client import minio_client # Импортируем Minio клиент


router = APIRouter()


# --- Workflow Templates ---
@router.post(
    "/workflow_templates/",
    response_model=WorkflowTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый шаблон рабочего процесса",
    description="Создает новый шаблон рабочего процесса с указанным названием и описанием."
)
async def create_template(
    template_in: WorkflowTemplateCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user), # Зависимость от авторизованного пользователя
):
    existing_template = await crud_workflow.get_workflow_template_by_name(db, name=template_in.name)
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Шаблон с таким названием уже существует."
        )
    
    db_template = await crud_workflow.create_workflow_template(db, template_in=template_in)
    return db_template


@router.get(
    "/workflow_templates/{template_id}",
    response_model=WorkflowTemplateRead,
    summary="Получить шаблон рабочего процесса по ID",
    description="Возвращает детали шаблона рабочего процесса, включая его шаги."
)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    template = await db.execute(
        select(WorkflowTemplate)
        .options(selectinload(WorkflowTemplate.steps))
        .where(WorkflowTemplate.id == template_id)
    )
    db_template = template.scalar_one_or_none()
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон рабочего процесса не найден."
        )
    return db_template


@router.get(
    "/workflow_templates/",
    response_model=List[WorkflowTemplateRead],
    summary="Получить список всех шаблонов рабочих процессов",
    description="Возвращает список всех доступных шаблонов рабочих процессов."
)
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    templates = await crud_workflow.get_workflow_templates(db, skip=skip, limit=limit)
    return templates


# --- Workflow Steps (nested under templates) ---
@router.post(
    "/workflow_templates/{template_id}/steps/",
    response_model=WorkflowStepRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить шаг к шаблону рабочего процесса",
    description="Добавляет новый шаг к существующему шаблону рабочего процесса."
)
async def add_step_to_template(
    template_id: int,
    step_in: WorkflowStepCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    template = await crud_workflow.get_workflow_template(db, template_id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон рабочего процесса не найден."
        )
    
    db_step = await crud_workflow.create_workflow_step(db, step_in=step_in, template_id=template_id)
    return db_step


@router.get(
    "/workflow_steps/{step_id}",
    response_model=WorkflowStepRead,
    summary="Получить шаг рабочего процесса по ID",
    description="Возвращает детали конкретного шага рабочего процесса."
)
async def get_step(
    step_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    step = await crud_workflow.get_workflow_step(db, step_id=step_id)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаг рабочего процесса не найден."
        )
    return step


# --- Workflow Instances ---
@router.post(
    "/workflow_instances/",
    response_model=WorkflowInstanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый экземпляр рабочего процесса",
    description="Создает новый экземпляр рабочего процесса на основе шаблона."
)
async def create_instance(
    instance_in: WorkflowInstanceCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    template = await crud_workflow.get_workflow_template(db, template_id=instance_in.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон рабочего процесса не найден."
        )
    
    db_instance = await crud_workflow.create_workflow_instance(
        db, instance_in=instance_in, created_by_id=current_user.id
    )
    return db_instance


@router.get(
    "/workflow_instances/{instance_id}",
    response_model=WorkflowInstanceRead,
    summary="Получить экземпляр рабочего процесса по ID",
    description="Возвращает детали экземпляра рабочего процесса, включая его текущий шаг, историю и вложения."
)
async def get_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    instance = await db.execute(
        select(WorkflowInstance)
        .options(
            selectinload(WorkflowInstance.template),
            selectinload(WorkflowInstance.current_step),
            selectinload(WorkflowInstance.created_by),
            selectinload(WorkflowInstance.history),
            selectinload(WorkflowInstance.attachments),
        )
        .where(WorkflowInstance.id == instance_id)
    )
    db_instance = instance.scalar_one_or_none()
    if not db_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Экземпляр рабочего процесса не найден."
        )
    return db_instance


# --- Attachments ---
@router.post(
    "/attachments/upload",
    response_model=AttachmentRead,
    summary="Загрузить файл и создать вложение",
    description="Загружает файл в MinIO и создает запись о вложении в базе данных."
)
async def upload_attachment(
    file: UploadFile = File(...),
    instance_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    file_path_in_minio = await minio_client.upload_file(file)

    db_attachment = await crud_workflow.create_attachment(
        db,
        attachment_in=AttachmentCreate(
            filename=file.filename,
            content_type=file.content_type,
        ),
        s3_path=file_path_in_minio,
        uploaded_by_id=current_user.id,
        instance_id=instance_id,
    )
    return db_attachment


@router.get(
    "/attachments/{attachment_id}/download",
    summary="Скачать файл вложения",
    description="Позволяет скачать файл, прикрепленный к рабочему процессу."
)
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    attachment = await crud_workflow.get_attachment(db, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вложение не найдено."
        )
    
    file_content = await minio_client.download_file(attachment.s3_path)
    return Response(content=file_content, media_type=attachment.content_type)


# --- Workflow Actions ---
class WorkflowActionRequest(BaseModel):
    comment: Optional[str] = Field(None, description="Комментарий к действию")

@router.post(
    "/workflow_instances/{instance_id}/approve",
    response_model=WorkflowInstanceRead,
    summary="Согласовать текущий шаг рабочего процесса",
)
async def approve_step(
    instance_id: int,
    action_in: WorkflowActionRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    instance = await db.get(WorkflowInstance, instance_id)
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Экземпляр не найден.")

    updated_instance = await crud_workflow.advance_workflow_instance(
        db, instance=instance, user=current_user, action="approve", comment=action_in.comment
    )
    return updated_instance


@router.post(
    "/workflow_instances/{instance_id}/reject",
    response_model=WorkflowInstanceRead,
    summary="Отклонить текущий шаг рабочего процесса",
)
async def reject_step(
    instance_id: int,
    action_in: WorkflowActionRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserRead = Depends(get_current_user),
):
    instance = await db.get(WorkflowInstance, instance_id)
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Экземпляр не найден.")

    updated_instance = await crud_workflow.advance_workflow_instance(
        db, instance=instance, user=current_user, action="reject", comment=action_in.comment
    )
    return updated_instance
