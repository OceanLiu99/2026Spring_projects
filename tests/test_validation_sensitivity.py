import pytest

from validation.sensitivity import correlation_report
from validation.sensitivity import sweep_attribute
from validation.sensitivity import validate_monotonic
from validation.sensitivity import value_as_number
from validation.simple_mock import simple_mock_run


def test_value_as_number_handles_bool_and_number():
    assert value_as_number(True) == 1.0
    assert value_as_number(False) == 0.0
    assert value_as_number(6) == 6.0


def test_sweep_attribute_luck_increases_max_depth():
    result = sweep_attribute(
        simple_mock_run,
        {"cell_id": "bomb_food", "use_bombs": True},
        "luck_level",
        (1, 4, 6),
        "max_depth",
        n_per_value=20,
        seed_start=3000,
    )

    assert len(result["rows"]) == 3
    assert result["rows"][0]["mean"] < result["rows"][1]["mean"]
    assert result["rows"][1]["mean"] < result["rows"][2]["mean"]


def test_sweep_attribute_bombs_increase_max_depth():
    result = sweep_attribute(
        simple_mock_run,
        {"cell_id": "bomb_food", "luck_level": 4},
        "use_bombs",
        (False, True),
        "max_depth",
        n_per_value=20,
        seed_start=4000,
    )

    assert result["rows"][0]["mean"] < result["rows"][1]["mean"]

def test_sweep_attribute_rejects_empty_values():
    with pytest.raises(ValueError):
        sweep_attribute(simple_mock_run, {}, "luck_level", (), "max_depth")

def test_correlation_report_returns_positive_luck_correlation():
    result = sweep_attribute(
        simple_mock_run,
        {"cell_id": "bomb_food", "use_bombs": True},
        "luck_level",
        (1, 4, 6),
        "max_depth",
        n_per_value=20,
        seed_start=5000,
    )
    report = correlation_report(result)

    assert report["r"] > 0.9 #random noise from simple_mock_run
    assert report["metric"] == "max_depth"


def test_validate_monotonic_passes_for_increasing_means():
    result = {
        "attr_name": "luck_level",
        "metric": "max_depth",
        "rows": [
            {"mean": 10.0},
            {"mean": 20.0},
            {"mean": 30.0},
        ],
    }

    summary = validate_monotonic(result, expected_sign="+")

    assert summary["passed"] is True


def test_validate_monotonic_rejects_bad_sign():
    result = {
        "attr_name": "luck_level",
        "metric": "max_depth",
        "rows": [
            {"mean": 30.0},
            {"mean": 20.0},
        ],
    }

    summary = validate_monotonic(result, expected_sign="+")

    assert summary["passed"] is False


