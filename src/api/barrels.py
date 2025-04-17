from dataclasses import dataclass
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

import sqlalchemy
from src.api import auth
from src import database as db
import random 

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int = Field(gt=0, description="Must be greater than 0")
    potion_type: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d] that sum to 1.0",
    )
    price: int = Field(ge=0, description="Price must be non-negative")
    quantity: int = Field(ge=0, description="Quantity must be non-negative")

    @field_validator("potion_type")
    @classmethod
    def validate_potion_type(cls, potion_type: List[float]) -> List[float]:
        if len(potion_type) != 4:
            raise ValueError("potion_type must have exactly 4 elements: [r, g, b, d]")
        if not abs(sum(potion_type) - 1.0) < 1e-6:
            raise ValueError("Sum of potion_type values must be exactly 1.0")
        return potion_type


class BarrelOrder(BaseModel):
    sku: str
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


@dataclass
class BarrelSummary:
    gold_paid: int
    ml_added_by_color: dict  # {"red": int, "green": int, "blue": int}


def _inv_row(connection) -> sqlalchemy.Row:
    return connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).one()

def calculate_barrel_summary(barrels: List[Barrel]) -> BarrelSummary:
    # return BarrelSummary(gold_paid=sum(b.price * b.quantity for b in barrels))
    gold = 0
    ml_by_color = {"red": 0, "green": 0, "blue": 0}
    for b in barrels:
        gold += b.price * b.quantity

        # assume only pure‑colour barrels (potion_type like [1,0,0,0])
        idx = b.potion_type.index(1)
        color = ("red", "green", "blue", "dark")[idx]
        if color in ml_by_color:
            ml_by_color[color] += b.ml_per_barrel * b.quantity
    return BarrelSummary(gold_paid=gold, ml_added_by_color=ml_by_color)


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_deliver_barrels(barrels_delivered: List[Barrel], order_id: int):
    """
    Processes barrels delivered based on the provided order_id. order_id is a unique value representing
    a single delivery; the call is idempotent based on the order_id.
    """
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    delivery = calculate_barrel_summary(barrels_delivered)

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
            #     """
            #     UPDATE global_inventory SET 
            #     gold = gold - :gold_paid
            #     """
            # ),
            # [{"gold_paid": delivery.gold_paid}],
                """
                UPDATE global_inventory
                SET gold       = gold - :gold_paid,
                    red_ml     = red_ml   + :add_r,
                    green_ml   = green_ml + :add_g,
                    blue_ml    = blue_ml  + :add_b
                """
            ),
            {
                "gold_paid": delivery.gold_paid,
                "add_r": delivery.ml_added_by_color["red"],
                "add_g": delivery.ml_added_by_color["green"],
                "add_b": delivery.ml_added_by_color["blue"],
            },
        )

    pass


def _cheapest_pure_colour(colour: str, catalog: List[Barrel]) -> Optional[Barrel]:
    colour_idx = {"red": 0, "green": 1, "blue": 2}[colour]
    pure = [b for b in catalog if b.potion_type[colour_idx] == 1]
    return min(pure, key=lambda b: b.price, default=None)

def create_barrel_plan(
    gold: int,
    current_red_potions: int,
    current_green_potions: int,
    current_blue_potions: int,
    wholesale_catalog: List[Barrel],
) -> List[BarrelOrder]:
    colour = random.choice(["red", "green", "blue"])
    potion_stock = {
        "red": current_red_potions,
        "green": current_green_potions,
        "blue": current_blue_potions,
    }

    if potion_stock[colour] >= 5:
        return []  # plenty in stock

    idx = {"red": 0, "green": 1, "blue": 2}[colour]
    candidates = [b for b in wholesale_catalog if b.potion_type[idx] == 1]
    if not candidates:
        return []

    # choose *smallest* then *cheapest* barrel we can afford
    candidates.sort(key=lambda b: (b.ml_per_barrel, b.price))
    chosen = next((b for b in candidates if b.price <= gold), None)

    return [BarrelOrder(sku=chosen.sku, quantity=1)] if chosen else []


@router.post("/plan", response_model=List[BarrelOrder])
def get_wholesale_purchase_plan(wholesale_catalog: List[Barrel]):
    """
    Gets the plan for purchasing wholesale barrels. The call passes in a catalog of available barrels
    and the shop returns back which barrels they'd like to purchase and how many.
    """

    print(f"barrel catalog: {wholesale_catalog}")

    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
               """
                SELECT gold, red_potions, green_potions, blue_potions
                FROM global_inventory
                """
            )
        ).one()

        
    return create_barrel_plan(
    gold=row.gold,
    current_red_potions=row.red_potions,
    current_green_potions=row.green_potions,
    current_blue_potions=row.blue_potions,
    wholesale_catalog=wholesale_catalog,
)
    # return create_barrel_plan(
    #     gold=row.gold,
    #     max_barrel_capacity=10000,  
    #     current_red_ml=row.red_ml,
    #     current_green_ml=row.green_ml,
    #     current_blue_ml=row.blue_ml,
    #     current_dark_ml=0,
    #     wholesale_catalog=wholesale_catalog,
    # )