import pytest
from validation.simple_mock import simple_mock_run
from validation.contract import result_dict_check

def test_simple_mock_same_seed_same_build_is_same():
    same_dict1 = simple_mock_run(2,{"cell_id": "bomb_food","luck_level": 6,"use_bombs": True})
    same_dict2 = simple_mock_run(2,{"cell_id": "bomb_food","luck_level": 6,"use_bombs": True})
    assert same_dict1 == same_dict2

def test_simple_mock_diff_seed_same_build_is_diff():
    run1_dict = simple_mock_run(1, {"cell_id": "bomb_food", "luck_level": 6, "use_bombs": True})
    run2_dict = simple_mock_run(2, {"cell_id": "bomb_food", "luck_level": 6, "use_bombs": True})
    assert run1_dict != run2_dict

def test_simple_mock_result_passes_contract():
    row = simple_mock_run(2,{"cell_id": "bomb_food","luck_level": 6,"use_bombs": True})
    result_dict_check(row)

def test_simple_mock_higher_luck_has_higher_depth():
    low_luck = simple_mock_run(2, {"cell_id": "bomb_food", "luck_level": 5, "use_bombs": True})
    high_luck = simple_mock_run(2, {"cell_id": "bomb_food", "luck_level": 6, "use_bombs": True})
    assert low_luck["max_depth"] < high_luck["max_depth"]

def test_simple_mock_bombs_increase_depth():
    no_bomb = simple_mock_run(2, {"cell_id": "pickaxe_nofood", "luck_level": 4, "use_bombs": False})
    bomb = simple_mock_run(2, {"cell_id": "bomb_nofood", "luck_level": 4, "use_bombs": True})
    assert no_bomb["max_depth"] < bomb["max_depth"]

def test_simple_mock_returns_required_keys():
    row = simple_mock_run(2, {"cell_id": "bomb_food", "luck_level": 6, "use_bombs": True})
    assert set(row.keys()) == {"seed", "cell_id", "luck_level", "max_depth", "net_profit", "died"}
