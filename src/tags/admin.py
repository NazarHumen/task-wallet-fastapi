from sqladmin import ModelView
from wtforms.validators import Length

from src.tags.models import Tag


class TagAdmin(ModelView, model=Tag):
    column_list = [Tag.id, Tag.name]
    column_searchable_list = [Tag.name]
    form_columns = [Tag.name]
    form_args = {"name": {"validators": [Length(min=1, max=50)]}}
