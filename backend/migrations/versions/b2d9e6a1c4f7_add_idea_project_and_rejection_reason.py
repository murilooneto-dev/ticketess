"""add idea project and rejection reason

Revision ID: b2d9e6a1c4f7
Revises: f47ac10b58cc
Create Date: 2026-08-19 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d9e6a1c4f7'
down_revision: Union[str, None] = 'f47ac10b58cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('project_ideas', sa.Column('project_id', sa.Integer(), nullable=True))
    op.add_column('project_ideas', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.create_foreign_key(
        'fk_project_ideas_project_id_projects',
        'project_ideas', 'projects',
        ['project_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_project_ideas_project_id_projects', 'project_ideas', type_='foreignkey')
    op.drop_column('project_ideas', 'rejection_reason')
    op.drop_column('project_ideas', 'project_id')
