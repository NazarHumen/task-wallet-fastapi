from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.auth.models import User
from src.tasks.models import Task, TaskStatus
from src.tasks.schemas import TaskCreate, TaskUpdate


def get_task(
    db: Session, task_id: int, *, for_update: bool = False
) -> Task | None:
    if for_update:
        return db.get(Task, task_id, with_for_update=True)
    return db.get(Task, task_id)


def create_task(db: Session, creator: User, data: TaskCreate) -> Task | None:
    creator = db.get(User, creator.id, with_for_update=True)
    if creator.balance < data.reward:
        return None
    creator.balance -= data.reward
    creator.reserved_balance += data.reward
    task = Task(
        title=data.title,
        description=data.description,
        reward=data.reward,
        creator_id=creator.id,
        status=TaskStatus.OPEN,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session, task: Task, creator: User, data: TaskUpdate
) -> Task | None:
    # `exclude_unset` distinguishes an omitted field from an explicit value,
    # so a PATCH only touches what the client actually sent.
    fields = data.model_dump(exclude_unset=True)

    if "reward" in fields and fields["reward"] != task.reward:
        # Changing the reward re-reserves the manager's balance by the delta.
        creator = db.get(User, creator.id, with_for_update=True)
        delta = fields["reward"] - task.reward
        if delta > 0:
            if creator.balance < delta:
                return None
            creator.balance -= delta
            creator.reserved_balance += delta
        else:
            creator.balance += -delta
            creator.reserved_balance -= -delta
        task.reward = fields["reward"]

    if "title" in fields:
        task.title = fields["title"]
    if "description" in fields:
        task.description = fields["description"]

    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    *,
    status: TaskStatus | None = None,
    creator_id: int | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Task], int]:
    conditions = []
    if status is not None:
        conditions.append(Task.status == status)
    if creator_id is not None:
        conditions.append(Task.creator_id == creator_id)
    if created_after is not None:
        conditions.append(Task.created_at >= created_after)
    if created_before is not None:
        conditions.append(Task.created_at <= created_before)

    total = db.scalar(
        select(func.count()).select_from(Task).where(*conditions)
    )
    items = db.scalars(
        select(Task)
        .where(*conditions)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total or 0


def assign_task(db: Session, task: Task, executor: User) -> Task:
    task.assignee_id = executor.id
    task.status = TaskStatus.IN_PROGRESS
    db.commit()
    db.refresh(task)
    return task


def submit_task(db: Session, task: Task) -> Task:
    task.status = TaskStatus.SUBMITTED
    db.commit()
    db.refresh(task)
    return task


def abandon_task(db: Session, task: Task) -> Task:
    # Executor drops the task: release it back to the pool. The manager's
    # reward stays reserved, so another executor can pick it up.
    task.assignee_id = None
    task.status = TaskStatus.OPEN
    db.commit()
    db.refresh(task)
    return task


def approve_task(
    db: Session, task: Task, manager: User, executor: User
) -> Task:
    # Lock both balances in a consistent order to avoid deadlocks.
    first, second = sorted((manager, executor), key=lambda u: u.id)
    db.get(User, first.id, with_for_update=True)
    db.get(User, second.id, with_for_update=True)
    manager.reserved_balance -= task.reward
    executor.balance += task.reward
    task.status = TaskStatus.COMPLETED
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()


def cancel_task(db: Session, task: Task, manager: User) -> Task:
    manager = db.get(User, manager.id, with_for_update=True)
    manager.reserved_balance -= task.reward
    manager.balance += task.reward
    task.status = TaskStatus.CANCELLED
    db.commit()
    db.refresh(task)
    return task
