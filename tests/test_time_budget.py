import pytest
from skull_cavern.time_budget import TimeBudget, ACTION_COSTS


def test_default_budget_is_1200():
    b = TimeBudget()
    assert b.remaining == 1200.0
    assert not b.is_exhausted()


def test_consume_decrements_and_clamps_to_zero():
    b = TimeBudget()
    b.consume(500)
    assert b.remaining == 700.0
    b.consume(800)
    assert b.remaining == 0.0
    assert b.is_exhausted()


def test_action_costs_match_spec_section_6_1():
    assert ACTION_COSTS["pickaxe_swing"] == 1.0
    assert ACTION_COSTS["place_bomb"] == 4.3
    assert ACTION_COSTS["combat_round"] == 0.7
    assert ACTION_COSTS["eat_food"] == 1.0
    assert ACTION_COSTS["descend_ladder"] == 2.0
    assert ACTION_COSTS["descend_shaft"] == 4.0
    assert ACTION_COSTS["move_per_rock"] == 0.5


def test_consume_negative_raises():
    b = TimeBudget()
    with pytest.raises(ValueError):
        b.consume(-1.0)
