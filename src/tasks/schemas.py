from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.tasks.models import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    reward: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    reward: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    reward: Decimal
    status: TaskStatus
    creator_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime | None


class TaskList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TaskRead]
