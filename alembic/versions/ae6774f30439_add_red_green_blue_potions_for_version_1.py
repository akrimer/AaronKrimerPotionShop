"""Add red, green, blue potions for version 1

Revision ID: ae6774f30439
Revises: e91d0c24f7d0
Create Date: 2025-04-16 12:12:29.772191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae6774f30439'
down_revision: Union[str, None] = 'e91d0c24f7d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("global_inventory", sa.Column("red_ml", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("global_inventory", sa.Column("green_ml", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("global_inventory", sa.Column("blue_ml", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("global_inventory", sa.Column("red_potions", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("global_inventory", sa.Column("green_potions", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("global_inventory", sa.Column("blue_potions", sa.Integer(), nullable=False, server_default="0"))

    op.create_check_constraint("ck_red_ml_non_negative", "global_inventory", "red_ml >= 0")
    op.create_check_constraint("ck_green_ml_non_negative", "global_inventory", "green_ml >= 0")
    op.create_check_constraint("ck_blue_ml_non_negative", "global_inventory", "blue_ml >= 0")
    op.create_check_constraint("ck_red_potions_non_negative", "global_inventory", "red_potions >= 0")
    op.create_check_constraint("ck_green_potions_non_negative", "global_inventory", "green_potions >= 0")
    op.create_check_constraint("ck_blue_potions_non_negative", "global_inventory", "blue_potions >= 0")


def downgrade():
    op.drop_constraint("ck_red_ml_non_negative", "global_inventory", type_="check")
    op.drop_constraint("ck_green_ml_non_negative", "global_inventory", type_="check")
    op.drop_constraint("ck_blue_ml_non_negative", "global_inventory", type_="check")
    op.drop_constraint("ck_red_potions_non_negative", "global_inventory", type_="check")
    op.drop_constraint("ck_green_potions_non_negative", "global_inventory", type_="check")
    op.drop_constraint("ck_blue_potions_non_negative", "global_inventory", type_="check")

    op.drop_column("global_inventory", "red_ml")
    op.drop_column("global_inventory", "green_ml")
    op.drop_column("global_inventory", "blue_ml")
    op.drop_column("global_inventory", "red_potions")
    op.drop_column("global_inventory", "green_potions")
    op.drop_column("global_inventory", "blue_potions")
