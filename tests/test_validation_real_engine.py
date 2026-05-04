"""Tests for the real engine adapter used by Phase 2 validation."""

import pytest

from validation.contract import result_dict_check
from validation.real_engine import real_engine_run

def test_real_engine_run_rejects_missing_cell_id():
    with pytest.raises(ValueError):
        real_engine_run(0, {"luck_level": 4})


def test_real_engine_run_rejects_missing_luck_level():
    with pytest.raises(ValueError):
        real_engine_run(0, {"cell_id": "pickaxe_nofood"})


def test_real_engine_run_returns_required_keys():
    row = real_engine_run(0, {"cell_id": "pickaxe_nofood", "luck_level": 4})

    result_dict_check(row)


def test_real_engine_run_keeps_build_context():
    row = real_engine_run(0, {"cell_id": "bomb_nofood", "luck_level": 6})

    assert row["cell_id"] == "bomb_nofood"
    assert row["luck_level"] == 6


def test_real_engine_run_is_deterministic_for_same_seed():
    build = {"cell_id": "bomb_food", "luck_level": 4}

    row1 = real_engine_run(42, build)
    row2 = real_engine_run(42, build)

    assert row1["seed"] == row2["seed"]
    assert row1["max_depth"] == row2["max_depth"]
    assert row1["net_profit"] == row2["net_profit"]


def test_real_engine_run_different_seeds_change_result():
    build = {"cell_id": "bomb_food", "luck_level": 4}

    row1 = real_engine_run(1, build)
    row2 = real_engine_run(2, build)

    assert (row1["max_depth"], row1["net_profit"]) != (
        row2["max_depth"],row2["net_profit"],
    )




