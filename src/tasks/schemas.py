from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.tags.schemas import TagRead
from src.tasks.models import TaskStatus


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    reward: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    tag_ids: list[int] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    reward: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    # Omitted -> tags untouched; [] -> clears all; [ids] -> replaces the set.
    tag_ids: list[int] | None = Field(default=None)


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
    tags: list[TagRead]


class TaskList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TaskRead]
