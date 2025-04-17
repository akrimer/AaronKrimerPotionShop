from src.api.bottler import PotionMixes, create_bottle_plan


from typing import List


def test_bottle_red_potions() -> None:
    red_ml: int = 100
    green_ml: int = 0
    blue_ml: int = 0
    dark_ml: int = 0
    maximum_potion_capacity: int = 1000
    current_potion_inventory: List[PotionMixes] = []

    result = create_bottle_plan(
        red_ml=red_ml,
        green_ml=green_ml,
        blue_ml=blue_ml,
        dark_ml=dark_ml,
        maximum_potion_capacity=maximum_potion_capacity,
        current_potion_inventory=current_potion_inventory,
    )

    assert len(result) == 1
    assert result[0].potion_type == [100, 0, 0, 0]
    assert result[0].quantity == 5



def test_bottle_red_potions_2() -> None:
    """
    500 ml of red should bottle into 5 pure‑red potions.
    """
    plan = create_bottle_plan(
        red_ml=500,
        green_ml=0,
        blue_ml=0,
        maximum_potion_capacity=100,   # plenty of capacity
        current_potion_inventory=[],
    )

    assert len(plan) == 1
    assert plan[0].potion_type == [100, 0, 0, 0]
    assert plan[0].quantity == 500 // ML_PER_POTION   # 5 bottles