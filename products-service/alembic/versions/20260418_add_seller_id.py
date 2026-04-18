"""add seller_id to products

Revision ID: 20260418_add_seller_id
Revises: d6d5ca6e1e16
Create Date: 2026-04-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260418_add_seller_id"
down_revision: Union[str, Sequence[str], None] = "d6d5ca6e1e16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("seller_id", sa.Integer(), nullable=False))


def downgrade() -> None:
    op.drop_column("products", "seller_id")

