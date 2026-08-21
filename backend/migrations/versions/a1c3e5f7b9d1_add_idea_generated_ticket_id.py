"""add idea generated_ticket_id

Revision ID: a1c3e5f7b9d1
Revises: b2d9e6a1c4f7
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3e5f7b9d1'
down_revision: Union[str, None] = 'b2d9e6a1c4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('project_ideas', sa.Column('generated_ticket_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_project_ideas_generated_ticket_id_tickets',
        'project_ideas', 'tickets',
        ['generated_ticket_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_project_ideas_generated_ticket_id_tickets', 'project_ideas', type_='foreignkey')
    op.drop_column('project_ideas', 'generated_ticket_id')
