"""remove project ideas and technical report

Revision ID: 5ff54f1175de
Revises: c398ccb256a1
Create Date: 2026-09-14 12:53:27.316951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ff54f1175de'
down_revision: Union[str, None] = 'c398ccb256a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('project_ideas')

    # só sobra o relatório de acompanhamento — remove as linhas técnicas
    # antes de derrubar a coluna, senão os pares técnico/gerencial do
    # mesmo período viram duplicata sob a nova regra de "1 por período"
    op.execute("DELETE FROM reports WHERE type = 'TECHNICAL'")
    with op.batch_alter_table('reports') as batch_op:
        batch_op.drop_column('type')


def downgrade() -> None:
    with op.batch_alter_table('reports') as batch_op:
        batch_op.add_column(
            sa.Column('type', sa.Enum('TECHNICAL', 'MANAGEMENT', name='reporttype'), nullable=True)
        )
    op.execute("UPDATE reports SET type = 'MANAGEMENT'")
    with op.batch_alter_table('reports') as batch_op:
        batch_op.alter_column('type', existing_type=sa.Enum('TECHNICAL', 'MANAGEMENT', name='reporttype'), nullable=False)

    op.create_table(
        'project_ideas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=160), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column(
            'status', sa.Enum('PENDENTE', 'APROVADA', 'REJEITADA', name='projectideastatus'), nullable=False
        ),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('generated_ticket_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['generated_ticket_id'], ['tickets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
