from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import sqlalchemy as sa
from src.api import auth
from enum import Enum
from typing import List, Optional
from src import database as db
from enum import Enum
from src.api.catalog import PRICE_PER_POTION, POTION_TYPE_LOOKUP  
from src.api.bottler import DARK_RECIPE  

router = APIRouter(
   prefix="/carts",
   tags=["cart"],
   dependencies=[Depends(auth.get_api_key)],
)



class Customer(BaseModel):
    customer_id: str
    customer_name: str = "anon"

class CartCreateResponse(BaseModel):
    cart_id: int

class CartItemDTO(BaseModel):
    quantity: int = Field(ge=1)

class CheckoutResponse(BaseModel):
    total_potions_bought: int
    total_gold_paid: int

def _recipe_row(conn, sku: str):
    return conn.execute(
        sa.text("SELECT id, price, inventory FROM potion_recipes WHERE sku=:s"),
        {"s": sku},
    ).mappings().first()

#creating new cart
@router.post("/", response_model=CartCreateResponse)
def create_cart(customer: Customer):
    with db.engine.begin() as conn:
        cart_id = conn.execute(
            sa.text(
                """
                INSERT INTO carts (customer_id, customer_name)
                VALUES (:cid, :cname)
                RETURNING id
                """
            ),
            {"cid": customer.customer_id, "cname": customer.customer_name},
        ).scalar_one()
    return CartCreateResponse(cart_id=cart_id)

# Add //update new cart
@router.post("/{cart_id}/items/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def set_item_quantity(cart_id: int, sku: str, item: CartItemDTO):
    with db.engine.begin() as conn:
        recipe = _recipe_row(conn, sku)
        if recipe is None:
            raise HTTPException(404, "Unknown SKU")

        conn.execute(
            sa.text(
                """
                INSERT INTO cart_items (cart_id, recipe_id, quantity)
                VALUES (:cid, :rid, :qty)
                ON CONFLICT (cart_id, recipe_id)
                DO UPDATE SET quantity = EXCLUDED.quantity
                """
            ),
            {"cid": cart_id, "rid": recipe["id"], "qty": item.quantity},
        )

# Ccheeckkoouut
@router.post("/{cart_id}/checkout", response_model=CheckoutResponse)
def checkout(cart_id: int):
    with db.engine.begin() as conn:
        items = conn.execute(
            sa.text(
                """
                SELECT pr.id AS recipe_id,
                       pr.price,
                       pr.inventory,
                       ci.quantity
                FROM cart_items ci
                JOIN potion_recipes pr ON pr.id = ci.recipe_id
                WHERE ci.cart_id = :cid
                """
            ),
            {"cid": cart_id},
        ).mappings().all()

        if not items:
            raise HTTPException(400, "Cart empty or does not exist")

        # stock check
        for it in items:
            if it["quantity"] > it["inventory"]:
                raise HTTPException(400, "Not enough stock")

        total_paid   = sum(it["price"] * it["quantity"] for it in items)
        total_bought = sum(it["quantity"] for it in items)

        # deducting inventory
        for it in items:
            conn.execute(
                sa.text(
                    """
                    UPDATE potion_recipes
                    SET inventory = inventory - :qty
                    WHERE id = :rid
                    """
                ),
                {"qty": it["quantity"], "rid": it["recipe_id"]},
            )

        # Add gold to store
        conn.execute(
            sa.text("UPDATE global_inventory SET gold = gold + :g"),
            {"g": total_paid},
        )

        # Marking cart as checked‑out
        conn.execute(
            sa.text("UPDATE carts SET checked_out = TRUE WHERE id = :cid"),
            {"cid": cart_id},
        )

    return CheckoutResponse(
        total_potions_bought=total_bought,
        total_gold_paid=total_paid,
    )