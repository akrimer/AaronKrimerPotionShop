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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ML_PER_POTION = 100        # one bottle uses 100 ml total liquid
DARK_RECIPE   = [25, 25, 50, 0]   # r, g, b, d ‑‑ sums to 100

# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------
class PotionMixes(BaseModel):
    potion_type: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="[r, g, b, d] integers summing to 100",
    )
    quantity: int = Field(..., ge=1, le=10_000)

    @field_validator("potion_type")
    @classmethod
    def validate_potion_type(cls, pt: List[int]) -> List[int]:
        if sum(pt) != 100:
            raise ValueError("Sum of potion_type values must be exactly 100")
        return pt


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _ml_required(pt: List[int], qty: int) -> tuple[int, int, int]:
    """Return ml to subtract from red, green, blue for qty bottles of mix `pt`"""
    r = pt[0] * ML_PER_POTION // 100 * qty
    g = pt[1] * ML_PER_POTION // 100 * qty
    b = pt[2] * ML_PER_POTION // 100 * qty
    return r, g, b


def _pure_colour_index(pt: List[int]) -> int | None:
    if pt == [100, 0, 0, 0]:
        return 0
    if pt == [0, 100, 0, 0]:
        return 1
    if pt == [0, 0, 100, 0]:
        return 2
    return None


# ---------------------------------------------------------------------------
# Deliver endpoint
# ---------------------------------------------------------------------------
@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_deliver_bottles(potions_delivered: List[PotionMixes], order_id: int):
    """
    Record delivered bottles: subtract the used ml and increment the correct
    potion counters. Supports pure colours **and** DARK_RECIPE.
    """
    with db.engine.begin() as connection:
        for p in potions_delivered:
            r_ml, g_ml, b_ml = _ml_required(p.potion_type, p.quantity)

            # Which inventory column to increment?
            idx = _pure_colour_index(p.potion_type)
            if idx is None and p.potion_type != DARK_RECIPE:
                raise HTTPException(400, "Only pure colours or DARK_RECIPE supported")

            if idx is None:   # dark mix
                pot_field = "dark_potions"
            else:
                pot_field = ("red_potions", "green_potions", "blue_potions")[idx]

            connection.execute(
                sqlalchemy.text(
                    f"""
                    UPDATE global_inventory
                    SET red_ml   = red_ml   - :ur,
                        green_ml = green_ml - :ug,
                        blue_ml  = blue_ml  - :ub,
                        {pot_field} = {pot_field} + :qty
                    """
                ),
                {"ur": r_ml, "ug": g_ml, "ub": b_ml, "qty": p.quantity},
            )


# ---------------------------------------------------------------------------
# Planner – bottle DARK_RECIPE first, then pure colours
# ---------------------------------------------------------------------------
def create_bottle_plan(
    red_ml: int,
    green_ml: int,
    blue_ml: int,
    maximum_potion_capacity: int,
    current_potion_inventory: List[PotionMixes],
) -> List[PotionMixes]:
    plan: List[PotionMixes] = []
    used_capacity = sum(p.quantity for p in current_potion_inventory)
    capacity_left = max(0, maximum_potion_capacity - used_capacity)

    # Step 1 – dark recipe
    if capacity_left:
        max_from_r = red_ml   // (ML_PER_POTION * DARK_RECIPE[0] / 100) if DARK_RECIPE[0] else float("inf")
        max_from_g = green_ml // (ML_PER_POTION * DARK_RECIPE[1] / 100) if DARK_RECIPE[1] else float("inf")
        max_from_b = blue_ml  // (ML_PER_POTION * DARK_RECIPE[2] / 100) if DARK_RECIPE[2] else float("inf")
        qty_dark = int(min(max_from_r, max_from_g, max_from_b, capacity_left))

        if qty_dark:
            plan.append(PotionMixes(potion_type=DARK_RECIPE, quantity=qty_dark))
            capacity_left -= qty_dark
            red_ml   -= qty_dark * DARK_RECIPE[0] * ML_PER_POTION // 100
            green_ml -= qty_dark * DARK_RECIPE[1] * ML_PER_POTION // 100
            blue_ml  -= qty_dark * DARK_RECIPE[2] * ML_PER_POTION // 100

    # Step 2 – pure colours
    for colour, stock_ml in (("red", red_ml), ("green", green_ml), ("blue", blue_ml)):
        if capacity_left == 0:
            break
        qty = min(stock_ml // ML_PER_POTION, capacity_left)
        if qty:
            pt = {"red": [100, 0, 0, 0], "green": [0, 100, 0, 0], "blue": [0, 0, 100, 0]}[colour]
            plan.append(PotionMixes(potion_type=pt, quantity=qty))
            capacity_left -= qty

    return plan


# ---------------------------------------------------------------------------
# Plan endpoint
# ---------------------------------------------------------------------------
@router.post("/plan", response_model=List[PotionMixes])
def get_bottle_plan():
    """
    Mix **all** available ml each tick – DARK_RECIPE first, then pure colours.
    No database writes happen here.
    """
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text("SELECT red_ml, green_ml, blue_ml FROM global_inventory")
        ).one()

    return create_bottle_plan(
        red_ml=row.red_ml,
        green_ml=row.green_ml,
        blue_ml=row.blue_ml,
        maximum_potion_capacity=50,
        current_potion_inventory=[],
    )










# from fastapi import APIRouter, Depends, status
# from pydantic import BaseModel, Field, field_validator
# from typing import List
# from src.api import auth

# import sqlalchemy as sa
# from src import database as db


# router = APIRouter(
#     prefix="/bottler",
#     tags=["bottler"],
#     dependencies=[Depends(auth.get_api_key)],
# )


# ML_PER_POTION = 100

# DARK_RECIPE = [25, 25, 50, 0]

# class PotionMixes(BaseModel):
#     potion_type: List[int] = Field(
#         ...,
#         min_length=4,
#         max_length=4,
#         description="Must contain exactly 4 elements: [r, g, b, d]",
#     )
#     quantity: int = Field(
#         ..., ge=1, le=10000, description="Quantity must be between 1 and 10,000"
#     )

#     @field_validator("potion_type")
#     @classmethod
#     def validate_potion_type(cls, potion_type: List[int]) -> List[int]:
#         if sum(potion_type) != 100:
#             raise ValueError("Sum of potion_type values must be exactly 100")
#         return potion_type
    


# def _inv_row(connection) -> sqlalchemy.Row:
#     return connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).one()


# def _ml_required(pt: List[int], qty: int) -> tuple[int, int, int]:
#     """
#     Returns ml to subtract from red, green, blue for a given mix & qty.
#     """
#     r_ml = pt[0] * ML_PER_POTION // 100 * qty
#     g_ml = pt[1] * ML_PER_POTION // 100 * qty
#     b_ml = pt[2] * ML_PER_POTION // 100 * qty
#     return r_ml, g_ml, b_ml


# def _is_pure(pt: List[int]) -> bool:
#     return pt in ([100, 0, 0, 0], [0, 100, 0, 0], [0, 0, 100, 0])


# def _pure_colour_index(pt: List[int]) -> int | None:
#     if pt == [100, 0, 0, 0]:
#         return 0
#     if pt == [0, 100, 0, 0]:
#         return 1
#     if pt == [0, 0, 100, 0]:
#         return 2
#     return None

# def _pure_colour_mix(colour: str) -> List[int]:
#     return {
#         "red": [100, 0, 0, 0],
#         "green": [0, 100, 0, 0],
#         "blue": [0, 0, 100, 0],
#     }[colour]


# @router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
# def post_deliver_bottles(potions_delivered: List[PotionMixes], order_id: int):
#     """
#     Delivery of potions requested after plan. order_id is a unique value representing
#     a single delivery; the call is idempotent based on the order_id.
#     """
#     print(f"potions delivered: {potions_delivered} order_id: {order_id}")

#     # TODO: Record values of delivered potions in your database.
#     # TODO: Subtract ml based on how much delivered potions used.

# with db.engine.begin() as connection:
#         for p in potions_delivered:
#             r_ml, g_ml, b_ml = _ml_required(p.potion_type, p.quantity)

#             # Decide which potion counter to bump
#             pure_idx = _pure_colour_index(p.potion_type)
#             if pure_idx is not None:
#                 pot_field = ("red_potions", "green_potions", "blue_potions")[pure_idx]
#             else:
#                 pot_field = "dark_potions"  # requires column in DB!

#             conn.execute(
#                 sqlalchemy.text(
#                     f"""
#                     UPDATE global_inventory
#                     SET red_ml   = red_ml   - :ur,
#                         green_ml = green_ml - :ug,
#                         blue_ml  = blue_ml  - :ub,
#                         {pot_field} = {pot_field} + :qty
#                     """
#                 ),
#                 {"ur": r_ml, "ug": g_ml, "ub": b_ml, "qty": p.quantity},
#             )
#         pass


# def create_bottle_plan(
#     red_ml: int,
#     green_ml: int,
#     blue_ml: int,
#     dark_ml: int,
#     maximum_potion_capacity: int,
#     current_potion_inventory: List[PotionMixes],
# ) -> List[PotionMixes]:
    
#     plan: List[PotionMixes] = []

#     # compute how many bottles we can add before hitting capacity
#     used_capacity = sum(p.quantity for p in current_potion_inventory)
#     capacity_left = max(0, maximum_potion_capacity - used_capacity)

#     #dark recepeie
#     if capacity_left:
#         # calc how many bottles i can make from each colrd ml pool
#         max_from_r = red_ml   // (ML_PER_POTION * DARK_RECIPE[0] / 100) if DARK_RECIPE[0] else float("inf")
#         max_from_g = green_ml // (ML_PER_POTION * DARK_RECIPE[1] / 100) if DARK_RECIPE[1] else float("inf")
#         max_from_b = blue_ml  // (ML_PER_POTION * DARK_RECIPE[2] / 100) if DARK_RECIPE[2] else float("inf")
#         max_dark = int(min(max_from_r, max_from_g, max_from_b, capacity_left))
#         if max_dark:
#             plan.append(PotionMixes(potion_type=DARK_RECIPE, quantity=max_dark))
#             capacity_left -= max_dark
#             # adjust virtual ml pools so pure‑colour can see
#             red_ml   -= int(DARK_RECIPE[0] * ML_PER_POTION / 100) * max_dark
#             green_ml -= int(DARK_RECIPE[1] * ML_PER_POTION / 100) * max_dark
#             blue_ml  -= int(DARK_RECIPE[2] * ML_PER_POTION / 100) * max_dark


# #pure colrd

#     for colour, stock_ml in (
#         ("red", red_ml),
#         ("green", green_ml),
#         ("blue", blue_ml),
#     ):
#         if capacity_left == 0:
#             break
#         make_qty = min(stock_ml // ML_PER_POTION, capacity_left)
#         if make_qty:
#             pure_pt = {
#                 "red": [100, 0, 0, 0],
#                 "green": [0, 100, 0, 0],
#                 "blue": [0, 0, 100, 0],
#             }[colour]
#             plan.append(PotionMixes(potion_type=pure_pt, quantity=make_qty))
#             capacity_left -= make_qty

#         return plan
#     # # TODO: Create a real bottle plan logic
#     # return [
#     #     PotionMixes(
#     #         potion_type=[100, 0, 0, 0],
#     #         quantity=5,
#     #     )
#     # ]


# @router.post("/plan", response_model=List[PotionMixes])
# def get_bottle_plan():
#     """
#     Gets the plan for bottling potions.
#     Each bottle has a quantity of what proportion of red, green, blue, and dark potions to add.
#     Colors are expressed in integers from 0 to 100 that must sum up to exactly 100.
#     """

#     # TODO: Fill in values below based on what is in your database

#     with db.engine.begin() as connection:
#         row = connection.execute(
#             sqlalchemy.text(
#                 """
#                 SELECT red_ml,
#                        green_ml,
#                        blue_ml
#                 FROM global_inventory
#                 """
#             )
#         ).one()


#         return create_bottle_plan(
#         red_ml=row.red_ml,
#         green_ml=row.green_ml,
#         blue_ml=row.blue_ml,
#         dark_ml=0,
#         maximum_potion_capacity=50,
#         current_potion_inventory=[],
#     )


# if __name__ == "__main__":
#     print(get_bottle_plan())