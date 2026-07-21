"""add balance and reward check constraints

Revision ID: c7f2a91d4e63
Revises: 43c581a155e1
Create Date: 2026-07-20 14:20:11.482913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f2a91d4e63'
down_revision: Union[str, Sequence[str], None] = '43c581a155e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Written by hand: autogenerate does not diff check constraints, so the
    # ones declared in the models were never emitted to the database.
    op.create_check_constraint(
        'ck_users_balance_non_negative', 'users', 'balance >= 0'
    )
    op.create_check_constraint(
        'ck_users_reserved_balance_non_negative',
        'users',
        'reserved_balance >= 0',
    )
    op.create_check_constraint(
        'ck_tasks_reward_positive', 'tasks', 'reward > 0'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_tasks_reward_positive', 'tasks', type_='check')
    op.drop_constraint(
        'ck_users_reserved_balance_non_negative', 'users', type_='check'
    )
    op.drop_constraint('ck_users_balance_non_negative', 'users', type_='check')
