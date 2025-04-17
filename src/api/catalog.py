from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Annotated
import sqlalchemy as sa
from src import database as db
from src.api.bottler import DARK_RECIPE  # reusing the mix percentages


router = APIRouter()

#my constants for future reference 

PRICE_PER_POTION = {
    "RED_POTION": 50,
    "GREEN_POTION": 50,
    "BLUE_POTION": 50,
    "DARK_POTION": 75,  # set any price you like
}

POTION_TYPE_LOOKUP = {
    "RED_POTION": [100, 0, 0, 0],
    "GREEN_POTION": [0, 100, 0, 0],
    "BLUE_POTION": [0, 0, 100, 0],
    "DARK_POTION": DARK_RECIPE,
}


class CatalogItem(BaseModel):
    sku: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]{1,20}$")]
    name: str
    quantity: Annotated[int, Field(ge=1, le=10000)]
    price: Annotated[int, Field(ge=1, le=500)]
    potion_type: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d]",
    )


# Placeholder function, you will replace this with a database call
def _create_catalog() -> List[CatalogItem]:
    with db.engine.begin() as connection:
        row = connection.execute(
            sa.text(
                """
                SELECT red_potions, green_potions, blue_potions, dark_potions
                FROM global_inventory
                """
            )
        ).one()

    inventory_map = {
        "RED_POTION": row.red_potions,
        "GREEN_POTION": row.green_potions,
        "BLUE_POTION": row.blue_potions,
        "DARK_POTION": getattr(row, "dark_potions", 0),  # dark column added in migration
    }

    items: List[CatalogItem] = []
    for sku, qty in (
        ("RED_POTION",  row.red_potions),
        ("GREEN_POTION",row.green_potions),
        ("BLUE_POTION", row.blue_potions),
    ):
        if qty > 0:
            items.append(
            CatalogItem(
                sku=sku,
                name=sku.lower().replace("_", " "),
                quantity=qty,
                price=PRICE_PER_POTION[sku],
                potion_type=POTION_TYPE_LOOKUP[sku],
            )
        )
    # exchange rule - atmost 6 SKUs
    return items[:6]

@router.get("/catalog/", tags=["catalog"], response_model=List[CatalogItem])
def get_catalog() -> List[CatalogItem]:
    """
    Retrieves the catalog of items. Each unique item combination should have only a single price
    can have 6 potion skus offered in your catalog at a time
    """
    return create_catalog()
