"""replace item_id with product_id uuid

Revision ID: 20260418_item_to_product_uuid
Revises: fee5f33b3ea7
Create Date: 2026-04-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260418_item_to_product_uuid"
down_revision: Union[str, Sequence[str], None] = "fee5f33b3ea7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chats", sa.Column("product_id", sa.Uuid(), nullable=True))
    op.drop_column("chats", "item_id")
    op.alter_column("chats", "product_id", nullable=False)
    op.create_index(op.f("ix_chats_product_id"), "chats", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chats_product_id"), table_name="chats")
    op.add_column("chats", sa.Column("item_id", sa.Integer(), nullable=True))
    op.drop_column("chats", "product_id")
    op.alter_column("chats", "item_id", nullable=False)

