from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.engine import Engine

from src.auth.admin import RefreshTokenAdmin, UserAdmin
from src.tags.admin import TagAdmin
from src.tasks.admin import TaskAdmin
from src.transactions.admin import TransactionAdmin

admin_views = [
    UserAdmin,
    RefreshTokenAdmin,
    TaskAdmin,
    TagAdmin,
    TransactionAdmin,
]


def setup_admin(app: FastAPI, engine: Engine) -> None:
    admin = Admin(app, engine)
    for view in admin_views:
        admin.add_view(view)
