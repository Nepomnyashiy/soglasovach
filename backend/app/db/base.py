from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Импортируем все модели здесь, чтобы Alembic мог их "увидеть"
from app.models.user import User  # noqa
from app.models.workflow import WorkflowTemplate, WorkflowStep, WorkflowInstance, WorkflowHistory, Attachment  # noqa
