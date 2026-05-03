"""
Set up a simple engine for testing in validation before the real one is ready.
"""
import random
from validation.contract import result_dict_check

def simple_mock_run(seed: int, build: dict):
    """
    Return one fake but deterministic simulation result.

    >>> row = simple_mock_run(2,{"cell_id": "bomb_food","luck_level": 6,"use_bombs": True})
    >>> row["seed"]
    2
    >>> row["cell_id"]
    'bomb_food'
    >>> row["luck_level"]
    6
    """
    rng = random.Random(seed)

    cell_id = build.get("cell_id", "pickaxe_nofood")
    luck_level = build.get("luck_level", 4)
    use_bombs = build.get("use_bombs", False)
    bomb_bonus = 20 if use_bombs else 0
    max_depth = 40 + luck_level * 5 + bomb_bonus + rng.randint(1, 20)
    net_profit = max_depth * 25 + rng.randint(200, 300)
    died = build.get("died", False)

    mock_dict = {
        "seed": seed,
        "cell_id": cell_id,
        "luck_level": luck_level,
        "max_depth": max_depth,
        "net_profit": net_profit,
        "died": died,
    }
    result_dict_check(mock_dict)

    return mock_dict








