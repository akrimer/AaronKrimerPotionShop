
from typing import List

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

ML_PER_POTION = 100
DARK_RECIPE   = [25, 25, 50, 0]    #why not 


class PotionMixes(BaseModel):
    potion_type: List[int] = Field(
        ..., min_length=4, max_length=4, description="[r,g,b,d] sums to 100"
    )
    quantity: int = Field(..., ge=1, le=10_000)

    @field_validator("potion_type")
    def _sum_100(cls, v: List[int]):
        if sum(v) != 100:
            raise ValueError("potion_type must sum to 100")
        return v


# Helper to count mls
def _ml_required(pt: List[int], qty: int) -> tuple[int, int, int]:
    """Return (red_ml, green_ml, blue_ml) consumed for qty bottles."""
    r = pt[0] * ML_PER_POTION // 100 * qty
    g = pt[1] * ML_PER_POTION // 100 * qty
    b = pt[2] * ML_PER_POTION // 100 * qty
    return r, g, b


def _recipe_row(conn, pt: List[int]):
    """Get potion_recipes row that exactly matches pt = [r,g,b,d]."""
    return conn.execute(
        sa.text(
            """
            SELECT id FROM potion_recipes
            WHERE red_pct=:r AND green_pct=:g AND blue_pct=:b AND dark_pct=:d
            """
        ),
        {"r": pt[0], "g": pt[1], "b": pt[2], "d": pt[3]},
    ).scalar()


# Delivery by updateding ml and inventory
@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_deliver_bottles(potions_delivered: List[PotionMixes], order_id: int):
    with db.engine.begin() as conn:
        for p in potions_delivered:
            recipe_id = _recipe_row(conn, p.potion_type)
            if recipe_id is None:
                raise HTTPException(400, "Recipe not found in potion_recipes")

            r_ml, g_ml, b_ml = _ml_required(p.potion_type, p.quantity)

            conn.execute(
                sa.text(
                    """
                    UPDATE global_inventory
                    SET red_ml   = red_ml   - :rml,
                        green_ml = green_ml - :gml,
                        blue_ml  = blue_ml  - :bml
                    """
                ),
                {"rml": r_ml, "gml": g_ml, "bml": b_ml},
            )

            conn.execute(
                sa.text(
                    """
                    UPDATE potion_recipes
                    SET inventory = inventory + :qty
                    WHERE id = :rid
                    """
                ),
                {"qty": p.quantity, "rid": recipe_id},
            )


# my plan  = mix every recipe until no more capacity
def create_bottle_plan(
    red_ml: int,
    green_ml: int,
    blue_ml: int,
    max_capacity: int,
) -> List[PotionMixes]:
    plan: list[PotionMixes] = []

    with db.engine.begin() as conn:
        recipes = conn.execute(
            sa.text("SELECT red_pct, green_pct, blue_pct, dark_pct FROM potion_recipes")
        ).mappings().all()

    capacity_left = max_capacity
    for r in recipes:
        pt = [r["red_pct"], r["green_pct"], r["blue_pct"], r["dark_pct"]]

        max_by_colour = min(
            red_ml   // (ML_PER_POTION * pt[0] / 100) if pt[0] else float("inf"),
            green_ml // (ML_PER_POTION * pt[1] / 100) if pt[1] else float("inf"),
            blue_ml  // (ML_PER_POTION * pt[2] / 100) if pt[2] else float("inf"),
            capacity_left,
        )

        if max_by_colour > 0:
            plan.append(PotionMixes(potion_type=pt, quantity=max_by_colour))
            capacity_left -= max_by_colour
            red_ml   -= pt[0] * ML_PER_POTION // 100 * max_by_colour
            green_ml -= pt[1] * ML_PER_POTION // 100 * max_by_colour
            blue_ml  -= pt[2] * ML_PER_POTION // 100 * max_by_colour

        if capacity_left == 0:
            break

    return plan


# plan endpoint
@router.post("/plan", response_model=List[PotionMixes])
def get_bottle_plan():
    with db.engine.begin() as conn:
        inv = conn.execute(
            sa.text("SELECT red_ml, green_ml, blue_ml FROM global_inventory")
        ).one()

    return create_bottle_plan(
        red_ml=inv.red_ml,
        green_ml=inv.green_ml,
        blue_ml=inv.blue_ml,
        max_capacity=50,
    )
