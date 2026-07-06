from sqladmin import ModelView
from wtforms.validators import NumberRange, Email

from src.auth.models import User, RefreshToken


class UserAdmin(ModelView, model=User):
    can_create = False
    column_list = [User.id, User.email, User.role, User.balance,
                   User.reserved_balance, User.created_at]
    # Password hash must never be editable from the admin panel.
    form_excluded_columns = [User.hashed_password]
    form_args = {
        "balance": {"validators": [NumberRange(min=0)]},
        "reserved_balance": {"validators": [NumberRange(min=0)]},
        "email": {"validators": [Email()]},
    }


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    can_create = False
    column_list = [RefreshToken.id, RefreshToken.user_id,
                   RefreshToken.expires_at, RefreshToken.revoked,
                   RefreshToken.created_at]
    form_excluded_columns = [RefreshToken.token_hash]
