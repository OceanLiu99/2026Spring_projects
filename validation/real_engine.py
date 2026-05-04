"""Real engine adapter for Phase 2 validation."""

from experiments.runner import make_player
from skull_cavern.run import SkullCavernRun # real engine simulation
from validation.contract import result_dict_check

def real_engine_run(seed: int, build: dict):
    """Run one real Skull Cavern simulation using the validation engine shape.
    This function keeps the same signature as simple_mock_run(seed, build).
    Lets convergence, sample_size, and sensitivity switch from mock to
    real engine without rewriting their own loops.

    :param seed: integer seed passed to SkullCavernRun
    :param build: dict with "cell_id" and "luck_level"
    :return: result dict that passes result_dict_check

    >>> row = real_engine_run(0, {"cell_id": "pickaxe_nofood", "luck_level": 4})
    >>> row["seed"]
    0
    >>> row["cell_id"]
    'pickaxe_nofood'
    >>> row["luck_level"]
    4
    >>> "max_depth" in row and "net_profit" in row and "died" in row
    True
    """
    # condition check
    if "cell_id" not in build:
        raise ValueError("build must contain cell_id")
    if "luck_level" not in build:
        raise ValueError("build must contain luck_level")

    cell_id = build["cell_id"]
    luck_level = build["luck_level"]

    # real engine run
    player = make_player(luck_level=luck_level, cell_id=cell_id)
    result = SkullCavernRun(player, seed=seed).play()

    # match validation contract
    result_row = result.to_dict()
    # manually update meet the validation contract
    result_row["cell_id"] = cell_id
    result_row["luck_level"] = luck_level
    result_dict_check(result_row)

    return result_row
