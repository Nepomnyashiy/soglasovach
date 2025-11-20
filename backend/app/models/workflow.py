import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.models.user import User


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    steps = relationship("WorkflowStep", back_populates="template", cascade="all, delete-orphan")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)

    template_id = Column(UUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=False)
    template = relationship("WorkflowTemplate", back_populates="steps")

    # В реальной системе здесь может быть ссылка на роль (Role)
    # Для простоты пока оставим assignee_id, который может быть null
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assignee = relationship("User")


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, default="in_progress")

    template_id = Column(UUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=False)
    current_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Добавлены поля created_at и updated_at
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    template = relationship("WorkflowTemplate")
    current_step = relationship("WorkflowStep")
    created_by = relationship("User")

    history = relationship("WorkflowHistory", back_populates="instance", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="instance", cascade="all, delete-orphan")


class WorkflowHistory(Base):
    __tablename__ = "workflow_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String, nullable=False) # e.g., "created", "approved", "rejected"
    comment = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    instance = relationship("WorkflowInstance", back_populates="history")
    step = relationship("WorkflowStep")
    user = relationship("User")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    s3_path = Column(String, nullable=False, unique=True)
    content_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    instance = relationship("WorkflowInstance", back_populates="attachments")
    uploaded_by = relationship("User")
