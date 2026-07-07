from sqladmin import ModelView
from wtforms.validators import Email, NumberRange, ValidationError

from src.auth.models import RefreshToken, User
from src.auth.validators import normalize_email


def _normalize_email(form, field):
    """Apply the shared email normalization, surfacing errors in the form."""
    if not field.data:
        return
    try:
        field.data = normalize_email(field.data)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


class UserAdmin(ModelView, model=User):
    can_create = False
    column_list = [
        User.id,
        User.email,
        User.role,
        User.balance,
        User.reserved_balance,
        User.created_at,
    ]
    # Password hash must never be editable from the admin panel.
    form_excluded_columns = [User.hashed_password]
    form_args = {
        "balance": {"validators": [NumberRange(min=0)]},
        "reserved_balance": {"validators": [NumberRange(min=0)]},
        "email": {"validators": [Email(), _normalize_email]},
    }


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    can_create = False
    column_list = [
        RefreshToken.id,
        RefreshToken.user_id,
        RefreshToken.expires_at,
        RefreshToken.revoked,
        RefreshToken.created_at,
    ]
    form_excluded_columns = [RefreshToken.token_hash]
