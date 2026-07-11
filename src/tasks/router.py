from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import Role, User
from src.db.database import get_db
from src.tags import service as tag_service
from src.tasks import service
from src.tasks.models import TaskStatus
from src.tasks.schemas import TaskCreate, TaskList, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    tags, missing = tag_service.resolve_tags(db, data.tag_ids)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown tag_ids: {missing}",
        )
    task = service.create_task(db, manager, data, tags)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance to reserve the reward",
        )
    return task


@router.get("", response_model=TaskList)
def list_tasks(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    creator_id: int | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    if (
        created_after is not None
        and created_before is not None
        and created_after > created_before
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="created_after must not be later than created_before",
        )
    items, total = service.list_tasks(
        db,
        status=status_filter,
        creator_id=creator_id,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )
    return TaskList(total=total, limit=limit, offset=offset, items=items)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    task = service.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    task = service.get_task(db, task_id, for_update=True)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.creator_id != manager.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this task",
        )
    if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task cannot be edited",
        )
    if data.reward is not None and task.status != TaskStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reward can only be changed while the task is open",
        )
    tags = None
    if data.tag_ids is not None:
        tags, missing = tag_service.resolve_tags(db, data.tag_ids)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown tag_ids: {missing}",
            )
    updated = service.update_task(db, task, manager, data, tags)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance to increase the reward",
        )
    return updated


@router.post("/{task_id}/assign", response_model=TaskRead)
def assign_task(
    task_id: int,
    db: Session = Depends(get_db),
    executor: User = Depends(require_role(Role.EXECUTOR)),
):
    task = service.get_task(db, task_id, for_update=True)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.status != TaskStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not open for assignment",
        )
    return service.assign_task(db, task, executor)


@router.post("/{task_id}/submit", response_model=TaskRead)
def submit_task(
    task_id: int,
    db: Session = Depends(get_db),
    executor: User = Depends(require_role(Role.EXECUTOR)),
):
    task = service.get_task(db, task_id, for_update=True)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.assignee_id != executor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assignee of this task",
        )
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not in progress",
        )
    return service.submit_task(db, task)


@router.post("/{task_id}/abandon", response_model=TaskRead)
def abandon_task(
    task_id: int,
    db: Session = Depends(get_db),
    executor: User = Depends(require_role(Role.EXECUTOR)),
):
    task = service.get_task(db, task_id, for_update=True)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.assignee_id != executor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the assignee of this task",
        )
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not in progress",
        )
    return service.abandon_task(db, task)


@router.post("/{task_id}/approve", response_model=TaskRead)
def approve_task(
    task_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    task = service.get_task(db, task_id, for_update=True)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.creator_id != manager.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this task",
        )
    if task.status != TaskStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not awaiting approval",
        )
    executor = db.get(User, task.assignee_id)
    if executor is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task has no assignee"
        )
    return service.approve_task(db, task, manager, executor)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    task = service.get_task(db, task_id, for_update=True)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.creator_id != manager.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this task",
        )
    # Only terminal tasks can be deleted; the reward is already released, so
    # removing the row cannot strand the manager's reserved balance.
    if task.status not in (TaskStatus.CANCELLED, TaskStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only cancelled or completed tasks can be deleted",
        )
    service.delete_task(db, task)


@router.post("/{task_id}/cancel", response_model=TaskRead)
def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    task = service.get_task(db, task_id, for_update=True)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.creator_id != manager.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this task",
        )
    if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task cannot be cancelled",
        )
    return service.cancel_task(db, task, manager)
