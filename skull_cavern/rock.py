"""
Rock drop table for Skull Cavern. Refactored from the 2022 Rock class.

Loads sc_rock.csv (depth-band columns) once at import and exposes a sampler
that takes a numpy.random.Generator so the calling RNG stream is preserved.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROCK_PATH = Path(__file__).parent / "data" / "sc_rock_drop.csv"

# Load once at import; indexed by item name.
ROCK_DF = pd.read_csv(ROCK_PATH).set_index("item")


def depth_to_band(depth: int) -> str:
    """Map an integer depth to a column name in sc_rock.csv.

    >>> depth_to_band(1)
    'SC-Shallow'
    >>> depth_to_band(100)
    'SC-Deep'
    """
    if depth < 1:
        raise ValueError(f"depth must be >= 1; got {depth}")
    if depth <= 25:
        return "SC-Shallow"
    if depth <= 75:
        return "SC-Mid"
    if depth <= 150:
        return "SC-Deep"
    return "SC-Abyss"


class RockTable:
    """Wraps the rock-drop dataframe; one instance per process."""

    def __init__(self):
        self.df = ROCK_DF
        self.items = self.df.index.tolist()

    def sample(self, depth: int, rng) -> str:
        """Return one random rockdrop item name sampled by depth-band weights."""
        depth_col = depth_to_band(depth)
        weights = self.df[depth_col].to_numpy(dtype=float)
        weights = weights / weights.sum()
        # choose one item from the sc_rock.csv list based on the weights
        index = rng.choice(len(self.items), p=weights)
        return self.items[index]

    def value_of_drop(self, item: str, rng) -> int:
        """Sell value for one drop event of `item` (count * price)."""
        rock_row = self.df.loc[item]
        price = int(rock_row["price"])
        if price == 0:
            return 0
        low = int(rock_row["min_num"])
        high = int(rock_row["max_num"])
        count = int(rng.integers(low, high + 1))
        return count * price