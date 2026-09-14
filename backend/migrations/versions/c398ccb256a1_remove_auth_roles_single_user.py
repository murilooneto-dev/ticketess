"""remove auth roles single user

Revision ID: c398ccb256a1
Revises: a1c3e5f7b9d1
Create Date: 2026-09-14 10:20:24.799712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c398ccb256a1'
down_revision: Union[str, None] = 'a1c3e5f7b9d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tickets') as batch_op:
        batch_op.add_column(sa.Column('requester_name', sa.String(length=160), nullable=True))
        batch_op.drop_column('created_by')

    with op.batch_alter_table('ticket_comments') as batch_op:
        batch_op.drop_column('author_id')

    with op.batch_alter_table('ticket_attachments') as batch_op:
        batch_op.drop_column('uploaded_by')

    with op.batch_alter_table('ticket_history') as batch_op:
        batch_op.drop_column('author_id')

    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_column('manager_id')

    with op.batch_alter_table('project_updates') as batch_op:
        batch_op.drop_column('author_id')

    with op.batch_alter_table('project_ideas') as batch_op:
        batch_op.drop_column('created_by')

    with op.batch_alter_table('reports') as batch_op:
        batch_op.drop_column('generated_by')

    op.drop_table('notifications')
    op.drop_table('sessions')
    op.drop_table('users')


def downgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'GESTOR', 'OPERADOR', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sessions_token_hash'), 'sessions', ['token_hash'], unique=True)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'type',
            sa.Enum(
                'TICKET_CREATED', 'TICKET_UPDATED', 'TICKET_COMMENT', 'PROJECT_UPDATE',
                'PROJECT_IDEA_CREATED', 'PROJECT_IDEA_STATUS_CHANGED', name='notificationtype',
            ),
            nullable=False,
        ),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('link', sa.String(length=255), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('reports') as batch_op:
        batch_op.add_column(sa.Column('generated_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_reports_generated_by_users', 'users', ['generated_by'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('project_ideas') as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_project_ideas_created_by_users', 'users', ['created_by'], ['id'], ondelete='CASCADE',
        )

    with op.batch_alter_table('project_updates') as batch_op:
        batch_op.add_column(sa.Column('author_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_project_updates_author_id_users', 'users', ['author_id'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('projects') as batch_op:
        batch_op.add_column(sa.Column('manager_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_projects_manager_id_users', 'users', ['manager_id'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('ticket_history') as batch_op:
        batch_op.add_column(sa.Column('author_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_ticket_history_author_id_users', 'users', ['author_id'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('ticket_attachments') as batch_op:
        batch_op.add_column(sa.Column('uploaded_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_ticket_attachments_uploaded_by_users', 'users', ['uploaded_by'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('ticket_comments') as batch_op:
        batch_op.add_column(sa.Column('author_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_ticket_comments_author_id_users', 'users', ['author_id'], ['id'], ondelete='SET NULL',
        )

    with op.batch_alter_table('tickets') as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_tickets_created_by_users', 'users', ['created_by'], ['id'], ondelete='SET NULL',
        )
        batch_op.drop_column('requester_name')
