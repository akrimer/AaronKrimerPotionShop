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


class SearchSortOptions(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"


class SearchSortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class LineItem(BaseModel):
    line_item_id: int
    item_sku: str
    customer_name: str
    line_item_total: int
    timestamp: str


class SearchResponse(BaseModel):
    previous: Optional[str] = None
    next: Optional[str] = None
    results: List[LineItem]


@router.get("/search/", response_model=SearchResponse, tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: SearchSortOptions = SearchSortOptions.timestamp,
    sort_order: SearchSortOrder = SearchSortOrder.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.
    """
    return SearchResponse(
        previous=None,
        next=None,
        results=[
            LineItem(
                line_item_id=1,
                item_sku="1 oblivion potion",
                customer_name="Scaramouche",
                line_item_total=50,
                timestamp="2021-01-01T00:00:00Z",
            )
        ],
    )


cart_id_counter = 1
carts: dict[int, dict[str, int]] = {}


class Customer(BaseModel):
    customer_id: str
    customer_name: str
    character_class: str
    level: int = Field(ge=1, le=20)


@router.post("/visits/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_visits(visit_id: int, customers: List[Customer]):
    """
    Shares the customers that visited the store on that tick.
    """
    print(customers)
    pass


class CartCreateResponse(BaseModel):
    cart_id: int


@router.post("/", response_model=CartCreateResponse)
def create_cart(new_cart: Customer):
    """
    Creates a new cart for a specific customer.
    """
    global cart_id_counter
    cart_id = cart_id_counter
    cart_id_counter += 1
    carts[cart_id] = {}
    return CartCreateResponse(cart_id=cart_id)


class CartItem(BaseModel):
    quantity: int = Field(ge=1, description="Quantity must be at least 1")


@router.post("/{cart_id}/items/{item_sku}", status_code=status.HTTP_204_NO_CONTENT)
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    print(
        f"cart_id: {cart_id}, item_sku: {item_sku}, cart_item: {cart_item}, carts: {carts}"
    )
    if cart_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")

    carts[cart_id][item_sku] = cart_item.quantity
    return status.HTTP_204_NO_CONTENT


class CheckoutResponse(BaseModel):
    total_potions_bought: int
    total_gold_paid: int


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout", response_model=CheckoutResponse)
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Handles the checkout process for a specific cart.
    """

    if cart_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")

    order = carts[cart_id]
    if not order:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate totals
    total_gold_paid = sum(PRICE_PER_POTION[sku] * qty for sku, qty in order.items())
    total_potions_bought = sum(order.values())

    # Map SKU → column name in global_inventory
    pot_field_map = {
        "RED_POTION": "red_potions",
        "GREEN_POTION": "green_potions",
        "BLUE_POTION": "blue_potions",
        "DARK_POTION": "dark_potions",
    }

    with db.engine.begin() as connection:
        row = connection.execute(
            sa.text(
                """
                SELECT red_potions, green_potions, blue_potions,
                       COALESCE(dark_potions, 0) AS dark_potions,
                       gold
                FROM global_inventory
                """
            )
        ).one()

        # 1) Validate stock
        for sku, qty in order.items():
            if qty > getattr(row, pot_field_map[sku]):
                raise HTTPException(400, f"Not enough stock for {sku}")

        # 2) Deduct potions & add gold
        updates = {
            "red_delta": -order.get("RED_POTION", 0),
            "green_delta": -order.get("GREEN_POTION", 0),
            "blue_delta": -order.get("BLUE_POTION", 0),
            "dark_delta": -order.get("DARK_POTION", 0),
            "gold_delta": total_gold_paid,
        }

        conn.execute(
            sa.text(
                """
                UPDATE global_inventory
                SET red_potions   = red_potions   + :red_delta,
                    green_potions = green_potions + :green_delta,
                    blue_potions  = blue_potions  + :blue_delta,
                    dark_potions  = COALESCE(dark_potions,0) + :dark_delta,
                    gold          = gold + :gold_delta
                """
            ),
            updates,
        )

    # clear cart (idempotent)
    carts.pop(cart_id, None)

    return CheckoutResponse(
        total_potions_bought=total_potions_bought,
        total_gold_paid=total_gold_paid,
    )
