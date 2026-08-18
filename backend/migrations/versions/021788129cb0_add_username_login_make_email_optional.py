"""add username login, make email optional

Revision ID: 021788129cb0
Revises: 2a1a5680df76
Create Date: 2026-08-17 16:53:08.545597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '021788129cb0'
down_revision: Union[str, None] = '2a1a5680df76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. add the column as nullable first, so existing rows aren't rejected
    op.add_column('users', sa.Column('username', sa.String(length=80), nullable=True))

    # 2. backfill a username for any existing user, derived from their email
    #    (or a fallback based on id if no email was set)
    connection = op.get_bind()
    users_table = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('username', sa.String),
        sa.column('email', sa.String),
    )
    for user_id, email in connection.execute(sa.select(users_table.c.id, users_table.c.email)).fetchall():
        username = email.split('@')[0] if email else f'user{user_id}'
        connection.execute(
            users_table.update().where(users_table.c.id == user_id).values(username=username)
        )

    # 3. enforce NOT NULL + unique index, relax email, and widen the role enum
    #    (SQLite requires a table rebuild for these, hence batch mode)
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username', existing_type=sa.String(length=80), nullable=False)
        batch_op.alter_column('email', existing_type=sa.VARCHAR(length=255), nullable=True)
        batch_op.alter_column(
            'role',
            existing_type=sa.VARCHAR(length=6),
            type_=sa.Enum('ADMIN', 'GESTOR', 'OPERADOR', name='userrole'),
            existing_nullable=False,
        )
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))
        batch_op.alter_column(
            'role',
            existing_type=sa.Enum('ADMIN', 'GESTOR', 'OPERADOR', name='userrole'),
            type_=sa.VARCHAR(length=6),
            existing_nullable=False,
        )
        batch_op.alter_column('email', existing_type=sa.VARCHAR(length=255), nullable=False)
        batch_op.drop_column('username')
