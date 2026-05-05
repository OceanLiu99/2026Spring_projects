"""Economic model: upfront costs, net profit, starting inventory per cell."""

from pathlib import Path
import pandas as pd 

PRICE_PATH = Path(__file__).parent / "data" / "bomb_food_prices.csv"
PRICE_DF = pd.read_csv(PRICE_PATH).set_index("item")

# Default prices of bomb and spicy eel, future can add more items
PRICE_BOMB = PRICE_DF.loc["bomb", "price"]
PRICE_FOOD = PRICE_DF.loc["spicy_eel", "price"]

# Death penalty constants
# assumed: 70% of gross is kept
# proved: 1000g surgery fee from wiki
DEATH_REVENUE_KEEP = 0.70
DEATH_SURGERY_FEE = 1000

# Starting inventory by default (bomb 20, food 5)
STARTING_INVENTORY = {
    "pickaxe_nofood": (0, 0),
    "pickaxe_food": (0, 5),
    "bomb_nofood": (20, 0),
    "bomb_food": (20, 5),
}


def upfront_cost(bombs: int, food: int) -> int:
    """Gold spent before the run begins.

    >>> upfront_cost(20, 5)
    12875
    """
    return bombs * PRICE_BOMB + food * PRICE_FOOD


def net_profit(gross: float, cost: float, died: bool) -> float:
    """Apply death penalty (keep 70% of gross, plus 1000g surgery fee) and subtract upfront cost.

    >>> net_profit(5000, 875, died=False)
    4125.0
    >>> net_profit(5000, 875, died=True)
    1625.0
    """
    if died:
        keep = gross * DEATH_REVENUE_KEEP - DEATH_SURGERY_FEE
    else:
        keep = gross
    return float(keep - cost)


def starting_inventory(cell_id: str):
    """Return (bombs, food) for one of the 4 strategy cells.

    >>> starting_inventory("bomb_food")
    (20, 5)
    """
    if cell_id not in STARTING_INVENTORY:
        raise ValueError(f"unknown cell_id: {cell_id}")
    return STARTING_INVENTORY[cell_id]