"""add ticket finalized_at

Revision ID: f47ac10b58cc
Revises: e8f1c3a9b6d2
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f47ac10b58cc'
down_revision: Union[str, None] = 'e8f1c3a9b6d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('finalized_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'finalized_at')
