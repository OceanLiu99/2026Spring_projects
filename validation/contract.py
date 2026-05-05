"""Check engine result shape for Phase 2 validation."""

key_required = (
    "seed",
    "cell_id",
    "luck_level",
    "max_depth",
    "net_profit",
    "died",
)


def result_dict_check(result_dict):
    """Check one simulation result dict.

    >>> row = {"seed": 1, "cell_id": "pickaxe_nofood", "luck_level": 4, "max_depth": 80, "net_profit": 1200, "died": False}
    >>> result_dict_check(row)
    """
    if not isinstance(result_dict, dict):
        raise ValueError("engine result must be a dict")

    missing_keys = []
    for key in key_required:
        if key not in result_dict:
            missing_keys.append(key)

    if missing_keys:
        raise ValueError(f"result missing required keys: {missing_keys}")