from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
import sqlalchemy as sa
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)


class InventoryAudit(BaseModel):
    number_of_potions: int
    ml_in_barrels: int
    gold: int


class CapacityPlan(BaseModel):
    potion_capacity: int = Field(
        ge=0, le=10, description="Potion capacity units, max 10"
    )
    ml_capacity: int = Field(ge=0, le=10, description="ML capacity units, max 10")

def _ensure_inventory_row(conn) -> sa.Row:
    """
    Make sure there is exactly one row in global_inventory and return it.
    """
    row = conn.execute(
        sa.text("SELECT * FROM global_inventory LIMIT 1")
    ).fetchone()

    if row is None:
        # fresh database: insert the singleton row with gold = 0
        conn.execute(sa.text("INSERT INTO global_inventory (gold) VALUES (0)"))
        row = conn.execute(
            sa.text("SELECT * FROM global_inventory LIMIT 1")
        ).one()

    return row

@router.get("/audit", response_model=InventoryAudit)
def get_inventory():
    """
    Returns a snapshot of the current inventory, fully backed by the database.
    """
    with db.engine.begin() as conn:
        row = _ensure_inventory_row(conn)

        ml_total = row.red_ml + row.green_ml + row.blue_ml
        pot_total = row.red_potions + row.green_potions + row.blue_potions

        return InventoryAudit(
            number_of_potions=pot_total,
            ml_in_barrels=ml_total,
            gold=row.gold,
        )


@router.post("/plan", response_model=CapacityPlan)
def get_capacity_plan():
    """
    Provides a daily capacity purchase plan.

    - Start with 1 capacity for 50 potions and 1 capacity for 10,000 ml of potion.
    - Each additional capacity unit costs 1000 gold.
    """
    return CapacityPlan(potion_capacity=0, ml_capacity=0)


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def deliver_capacity_plan(capacity_purchase: CapacityPlan, order_id: int):
    # """
    # Processes the delivery of the planned capacity purchase. order_id is a
    # unique value representing a single delivery; the call is idempotent.

    # - Start with 1 capacity for 50 potions and 1 capacity for 10,000 ml of potion.
    # - Each additional capacity unit costs 1000 gold.
    # """
    # print(f"capacity delivered: {capacity_purchase} order_id: {order_id}")
    pass
