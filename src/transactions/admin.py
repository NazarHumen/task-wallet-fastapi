from sqladmin import ModelView

from src.transactions.models import Transaction


class TransactionAdmin(ModelView, model=Transaction):
    # Ledger is append-only and system-generated; keep it read-only.
    can_create = False
    can_edit = False
    can_delete = False

    column_list = [
        Transaction.id,
        Transaction.user_id,
        Transaction.type,
        Transaction.amount,
        Transaction.balance_after,
        Transaction.task_id,
        Transaction.created_at,
    ]
    column_searchable_list = [Transaction.type]
