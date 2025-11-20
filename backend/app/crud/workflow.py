from typing import List, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from app.models.workflow import (
    WorkflowTemplate,
    WorkflowStep,
    WorkflowInstance,
    WorkflowHistory,
    Attachment,
)
from app.schemas.workflow import (
    WorkflowTemplateCreate,
    WorkflowStepCreate,
    WorkflowInstanceCreate,
    WorkflowHistoryCreate,
    AttachmentCreate,
)


# --- CRUD для WorkflowTemplate ---
async def create_workflow_template(
    db: AsyncSession, template_in: WorkflowTemplateCreate
) -> WorkflowTemplate:
    db_template = WorkflowTemplate(**template_in.model_dump())
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    return db_template


async def get_workflow_template(db: AsyncSession, template_id: uuid.UUID) -> Optional[WorkflowTemplate]:
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
    )
    return result.scalar_one_or_none()


async def get_workflow_templates(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[WorkflowTemplate]:
    result = await db.execute(
        select(WorkflowTemplate).offset(skip).limit(limit)
    )
    return result.scalars().all()


# Получение WorkflowTemplate по имени
async def get_workflow_template_by_name(db: AsyncSession, name: str) -> Optional[WorkflowTemplate]:
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.name == name)
    )
    return result.scalar_one_or_none()


# --- CRUD для WorkflowStep ---
async def create_workflow_step(
    db: AsyncSession, step_in: WorkflowStepCreate, template_id: uuid.UUID
) -> WorkflowStep:
    db_step = WorkflowStep(**step_in.model_dump(), template_id=template_id)
    db.add(db_step)
    await db.commit()
    await db.refresh(db_step)
    return db_step


async def get_workflow_step(db: AsyncSession, step_id: uuid.UUID) -> Optional[WorkflowStep]:
    result = await db.execute(
        select(WorkflowStep).where(WorkflowStep.id == step_id)
    )
    return result.scalar_one_or_none()


async def get_workflow_steps_by_template(
    db: AsyncSession, template_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[WorkflowStep]:
    result = await db.execute(
        select(WorkflowStep)
        .where(WorkflowStep.template_id == template_id)
        .order_by(WorkflowStep.order)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


# --- CRUD для WorkflowInstance ---
async def create_workflow_instance(
    db: AsyncSession, instance_in: WorkflowInstanceCreate, created_by_id: uuid.UUID
) -> WorkflowInstance:
    # При создании экземпляра, первый шаг должен быть установлен автоматически
    # Предполагаем, что шаблон имеет хотя бы один шаг
    first_step_result = await db.execute(
        select(WorkflowStep)
        .where(WorkflowStep.template_id == instance_in.template_id)
        .order_by(WorkflowStep.order)
        .limit(1)
    )
    first_step = first_step_result.scalar_one_or_none()
    if not first_step:
        raise ValueError("Workflow template must have at least one step.")

    db_instance = WorkflowInstance(
        template_id=instance_in.template_id,
        created_by_id=created_by_id,
        current_step_id=first_step.id,
        status="in_progress",
    )
    db.add(db_instance)
    await db.commit()
    await db.refresh(db_instance)

    # Добавление вложений, если они были указаны
    if instance_in.attachment_ids:
        for att_id in instance_in.attachment_ids:
            # Нужно загрузить Attachment и обновить его instance_id
            att = await db.get(Attachment, att_id)
            if att:
                att.instance_id = db_instance.id
                db.add(att)
        await db.commit()
        await db.refresh(db_instance) # Обновить, чтобы подтянуть вложения

    return db_instance


async def get_workflow_instance(db: AsyncSession, instance_id: uuid.UUID) -> Optional[WorkflowInstance]:
    result = await db.execute(
        select(WorkflowInstance)
        .where(WorkflowInstance.id == instance_id)
    )
    return result.scalar_one_or_none()


# --- CRUD для WorkflowHistory ---
async def create_workflow_history_entry(
    db: AsyncSession,
    history_in: WorkflowHistoryCreate,
    instance_id: uuid.UUID,
    step_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkflowHistory:
    db_history = WorkflowHistory(
        **history_in.model_dump(),
        instance_id=instance_id,
        step_id=step_id,
        user_id=user_id,
    )
    db.add(db_history)
    await db.commit()
    await db.refresh(db_history)
    return db_history


async def get_workflow_history_for_instance(
    db: AsyncSession, instance_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[WorkflowHistory]:
    result = await db.execute(
        select(WorkflowHistory)
        .where(WorkflowHistory.instance_id == instance_id)
        .order_by(WorkflowHistory.timestamp)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


# --- CRUD для Attachment ---
async def create_attachment(
    db: AsyncSession,
    attachment_in: AttachmentCreate,
    s3_path: str,
    uploaded_by_id: uuid.UUID,
    instance_id: Optional[uuid.UUID] = None, # Может быть прикреплено позже
) -> Attachment:
    db_attachment = Attachment(
        **attachment_in.model_dump(),
        s3_path=s3_path,
        uploaded_by_id=uploaded_by_id,
        instance_id=instance_id,
    )
    db.add(db_attachment)
    await db.commit()
    await db.refresh(db_attachment)
    return db_attachment


async def get_attachment(db: AsyncSession, attachment_id: uuid.UUID) -> Optional[Attachment]:
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    return result.scalar_one_or_none()


async def get_attachments_for_instance(
    db: AsyncSession, instance_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Attachment]:
    result = await db.execute(
        select(Attachment)
        .where(Attachment.instance_id == instance_id)
        .order_by(Attachment.uploaded_at)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def delete_attachment(db: AsyncSession, attachment_id: uuid.UUID) -> bool:
    result = await db.execute(
        delete(Attachment).where(Attachment.id == attachment_id)
    )
    await db.commit()
    return result.rowcount > 0
