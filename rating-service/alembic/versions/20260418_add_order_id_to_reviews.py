"""add order_id to reviews

Revision ID: 20260418_add_order_id_to_reviews
Revises: cb3097d76414
Create Date: 2026-04-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260418_add_order_id_to_reviews"
down_revision: Union[str, Sequence[str], None] = "cb3097d76414"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("order_id", sa.Integer(), nullable=False))
    op.create_index(op.f("ix_reviews_order_id"), "reviews", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviews_order_id"), table_name="reviews")
    op.drop_column("reviews", "order_id")

