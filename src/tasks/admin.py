from sqladmin import ModelView

from src.tasks.models import Task


class TaskAdmin(ModelView, model=Task):
    columns = [
        Task.id,
        Task.title,
        Task.description,
        Task.reward,
        Task.status,
        Task.creator_id,
        Task.assignee_id,
        Task.created_at,
    ]
