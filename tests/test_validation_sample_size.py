import pytest

from validation.sample_size import ci_half_width
from validation.sample_size import recommend_n
from validation.sample_size import sweep_n
from validation.simple_mock import simple_mock_run


def test_ci_half_width_hand_calculated_five_samples():
    half_width = ci_half_width([1.0, 2.0, 3.0, 4.0, 5.0])

    assert round(half_width, 3) == 1.963


def test_ci_half_width_rejects_single_sample():
    with pytest.raises(ValueError):
        ci_half_width([1.0])


def test_sweep_n_with_simple_mock_returns_one_row_per_grid_point():
    rows = sweep_n(
        simple_mock_run,
        {"cell_id": "bomb_food", "luck_level": 6, "use_bombs": True},
        "max_depth",
        n_grid=(5, 10),
        n_replicates=3,
        seed_start=1000,
    )

    assert len(rows) == 2
    assert rows[0]["n"] == 5
    assert rows[1]["n"] == 10
    assert "relative_half_width" in rows[0]


def test_recommend_n_returns_smallest_stable_n():
    rows = [
        {"n": 50, "relative_half_width": 0.08},
        {"n": 100, "relative_half_width": 0.04},
        {"n": 200, "relative_half_width": 0.03},
    ]

    assert recommend_n(rows, target_relative=0.05) == 100


def test_recommend_n_returns_none_when_target_too_strict():
    rows = [
        {"n": 50, "relative_half_width": 0.08},
        {"n": 100, "relative_half_width": 0.06},
        {"n": 200, "relative_half_width": 0.051},
    ]

    assert recommend_n(rows, target_relative=0.05) is None
