import numpy as np
import pytest
from skull_cavern.rock import RockTable, depth_to_band


def test_depth_to_band_boundaries():
    assert depth_to_band(1) == "SC-Shallow"
    assert depth_to_band(25) == "SC-Shallow"
    assert depth_to_band(26) == "SC-Mid"
    assert depth_to_band(75) == "SC-Mid"
    assert depth_to_band(76) == "SC-Deep"
    assert depth_to_band(150) == "SC-Deep"
    assert depth_to_band(151) == "SC-Abyss"
    assert depth_to_band(500) == "SC-Abyss"


def test_depth_to_band_rejects_zero_and_negative():
    with pytest.raises(ValueError):
        depth_to_band(0)


def test_table_has_expected_items():
    t = RockTable()
    assert "Stone" in t.items
    assert "Iridium Ore" in t.items
    assert "Prismatic Shard" in t.items


def test_sample_returns_known_item():
    t = RockTable()
    rng = np.random.default_rng(0)
    item = t.sample(depth=10, rng=rng)
    assert item in t.items


def test_iridium_more_likely_in_abyss_than_shallow():
    t = RockTable()
    rng = np.random.default_rng(123)
    shallow = sum(t.sample(depth=5, rng=rng) == "Iridium Ore" for _ in range(2000))
    rng = np.random.default_rng(123)
    abyss = sum(t.sample(depth=200, rng=rng) == "Iridium Ore" for _ in range(2000))
    assert abyss > shallow * 4


def test_value_of_drop_returns_int_with_count():
    t = RockTable()
    rng = np.random.default_rng(0)
    val = t.value_of_drop("Stone", rng=rng)
    assert val >= 2
    assert val <= 6