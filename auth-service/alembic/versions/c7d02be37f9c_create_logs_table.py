"""create logs table

Revision ID: c7d02be37f9c
Revises: 001_initial
Create Date: 2026-03-18 14:26:20.055019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d02be37f9c'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём таблицу logs
    op.create_table(
        'logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создаём индекс для быстрого поиска по user_id
    op.create_index('ix_logs_user_id', 'logs', ['user_id'], unique=False)
    op.create_index('ix_logs_created_at', 'logs', ['created_at'], unique=False)


def downgrade() -> None:
    # Удаляем таблицу logs
    op.drop_index('ix_logs_created_at', table_name='logs')
    op.drop_index('ix_logs_user_id', table_name='logs')
    op.drop_table('logs')
