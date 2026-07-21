from sqladmin import ModelView

from src.payments.models import Payment


class PaymentAdmin(ModelView, model=Payment):
    can_create = False
    can_edit = False
    can_delete = False

    column_list = [
        Payment.id,
        Payment.user_id,
        Payment.amount,
        Payment.status,
        Payment.stripe_session_id,
        Payment.transaction_id,
        Payment.created_at,
    ]
    column_searchable_list = [Payment.user_id]
