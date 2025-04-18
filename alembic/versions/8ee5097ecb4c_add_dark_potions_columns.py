"""Add dark potions columns

Revision ID: 8ee5097ecb4c
Revises: e5bebb7f40a2
Create Date: 2025-04-17 22:46:13.814379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ee5097ecb4c'
down_revision: Union[str, None] = 'e5bebb7f40a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   op.add_column("global_inventory",sa.Column("dark_ml", sa.Integer(), nullable=False, server_default="0"),)
   op.add_column("global_inventory",sa.Column("dark_potions", sa.Integer(), nullable=False, server_default="0"),)

   
   op.create_check_constraint("ck_dark_ml_non_negative", "global_inventory", "dark_ml >= 0")
   op.create_check_constraint("ck_dark_potions_non_negative", "global_inventory", "dark_potions >= 0")



def downgrade() -> None:
    op.drop_constraint("ck_dark_potions_non_negative", "global_inventory", type_="check")
    op.drop_constraint("ck_dark_ml_non_negative", "global_inventory", type_="check")
    
    op.drop_column("global_inventory", "dark_potions")
    op.drop_column("global_inventory", "dark_ml")