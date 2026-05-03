"""
Shared infrastructure for H1/H2/H3 experiment scripts.

Seed convention: each run is deterministic and identified by a unique integer seed.
    seed = experiment_id * 10000000 + cell_idx * 10000 + run_idx
"""
from pathlib import Path
import pandas as pd

from skull_cavern.player import Player
from skull_cavern.strategy import Strategy, BombStrategy, FoodStrategy
from skull_cavern.run import SkullCavernRun
from skull_cavern.economy import starting_inventory

# default equipment for all runs, which is the best equipment available in the game that a player can buy
EQUIPMENT = ["Space Boots", "Lava Katana", "", ""]
# default to skill level 7 (max is 10)
SKILL_LEVEL = 7

OUTPUTS_DATA = Path(__file__).resolve().parent.parent / "outputs" / "data"


def assert_equipment_present():
    """Fail if equipment rows are missing"""
    from skull_cavern.equipment import Equipment
    for name in ("Space Boots", "Lava Katana"):
        e = Equipment(name)
        if e.defense == 0 and e.damage_max == 0:
            raise RuntimeError(
                f"{name!r} not found in equipments_db.csv, it will cause zero stats."
            )


def make_player(luck_level: int, cell_id: str) -> Player:
    bombs, food = starting_inventory(cell_id)
    use_bombs = bombs > 0
    use_food = food > 0
    return Player(
        equipment_names=EQUIPMENT,
        skill_level=SKILL_LEVEL,
        luck_level=luck_level,
        bombs=bombs,
        food=food,
        strategy=Strategy(BombStrategy(use_bombs), FoodStrategy(use_food)),
    )


def run_cell(experiment_id: int, cell_idx: int, cell_id: str,
             luck_level: int, n_runs: int) -> pd.DataFrame:
    """Run n_runs deterministic simulations for one experimental cell."""
    rows = []
    for run_idx in range(n_runs):
        seed = experiment_id * 10000000 + cell_idx * 10000 + run_idx
        player = make_player(luck_level, cell_id)
        result = SkullCavernRun(player, seed=seed).play()
        d = result.to_dict()
        d["luck_level"] = luck_level
        d["experiment_id"] = experiment_id
        rows.append(d)
    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, filename: str) -> Path:
    OUTPUTS_DATA.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_DATA / filename
    df.to_csv(out, index=False)
    return out