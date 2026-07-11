from sqladmin import ModelView
from wtforms.validators import Length

from src.tasks.models import Task


class TaskAdmin(ModelView, model=Task):
    can_create = False
    can_delete = False

    column_list = [
        Task.id,
        Task.title,
        Task.description,
        Task.reward,
        Task.tags,
        Task.status,
        Task.creator_id,
        Task.assignee_id,
        Task.created_at,
    ]
    column_searchable_list = [Task.description, "tags.name"]
    form_columns = [Task.title, Task.description, Task.tags]
    form_args = {
        "title": {"validators": [Length(min=1, max=255)]},
        "description": {"validators": [Length(max=2000)]},
    }
