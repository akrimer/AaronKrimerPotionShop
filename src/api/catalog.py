from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Annotated
import sqlalchemy 
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



@router.get("/catalog/", tags=["catalog"], response_model=List[CatalogItem])
def get_catalog():
    with db.engine.begin() as connection:
        rows = connection.execute(sqlalchemy.text(
            "SELECT sku, name, price, red_pct, green_pct, blue_pct, dark_pct, inventory "
+           "FROM potion_recipes WHERE inventory > 0 LIMIT 6"
        )).mappings().all()

    return [
        CatalogItem(
            sku=row["sku"],
            name=row["name"],
            quantity=row["inventory"],
            price=row["price"],
            potion_type=[row["red_pct"], row["green_pct"],
                         row["blue_pct"], row["dark_pct"]],
        )
        for row in rows
    ]