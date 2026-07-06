from sqladmin import Admin
from sqlalchemy.engine import Engine
from fastapi import FastAPI
from src.auth.admin import UserAdmin, RefreshTokenAdmin

admin_views = [
    UserAdmin,
    RefreshTokenAdmin,

]


def setup_admin(app: FastAPI, engine: Engine) -> None:
    admin = Admin(app, engine)
    for view in admin_views:
        admin.add_view(view)
