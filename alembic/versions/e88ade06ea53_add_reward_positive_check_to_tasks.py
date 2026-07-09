"""add reward positive check to tasks

Revision ID: e88ade06ea53
Revises: ef38fd4dceee
Create Date: 2026-07-09 15:48:59.647733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e88ade06ea53'
down_revision: Union[str, Sequence[str], None] = 'ef38fd4dceee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
