import pytest
from validation.contract import result_dict_check

def test_validation_contract_no_missing_keys():
    row = {"seed": 1, "cell_id": "pickaxe_nofood", "luck_level": 4,
           "max_depth": 80, "net_profit": 1200, "died": False}
    result_dict_check(row)

def test_validation_contract_missing_key():
    row = {"seed": 1, "cell_id": "pickaxe_nofood"}
    with pytest.raises(ValueError):
        result_dict_check(row)
