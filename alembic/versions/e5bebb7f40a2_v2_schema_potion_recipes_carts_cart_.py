"""v2 schema: potion_recipes, carts, cart_items

Revision ID: e5bebb7f40a2
Revises: ae6774f30439
Create Date: 2025-04-16 23:32:14.792488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5bebb7f40a2'
down_revision: Union[str, None] = 'ae6774f30439'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table(
        "potion_recipes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sku", sa.String(32), unique=True, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("red_pct", sa.Integer, nullable=False),
        sa.Column("green_pct", sa.Integer, nullable=False),
        sa.Column("blue_pct", sa.Integer, nullable=False),
        sa.Column("dark_pct", sa.Integer, nullable=False),
        sa.Column("inventory", sa.Integer, nullable=False, server_default="0"),
        sa.CheckConstraint("red_pct+green_pct+blue_pct+dark_pct = 100"),
        sa.CheckConstraint("inventory >= 0"),
    )

    op.create_table(
        "carts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("customer_id", sa.String(64), nullable=False),
        sa.Column("customer_name", sa.String(64)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("checked_out", sa.Boolean, server_default=sa.text("FALSE")),
    )

    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cart_id", sa.Integer, sa.ForeignKey("carts.id", ondelete="CASCADE")),
        sa.Column("recipe_id", sa.Integer, sa.ForeignKey("potion_recipes.id")),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.CheckConstraint("quantity > 0"),
        sa.UniqueConstraint("cart_id", "recipe_id"),
    )

def downgrade():
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("potion_recipes")
