import numpy as np
import pytest
from skull_cavern.monster import (
    Monster, sample_monster, generate_monster_list, resolve_mummy_kill,
)


def test_purple_slime_stats():
    m = Monster("PurpleSlime")
    assert m.hp == 180
    assert m.damage == 14
    assert m.defense == 0


def test_serpent_stats():
    m = Monster("Serpent")
    assert m.hp == 90
    assert m.damage == 20


def test_mummy_revive_state_default():
    m = Monster("Mummy")
    assert m.revived_once is False
    assert not m.permanently_dead


def test_iridium_bat_stats():
    m = Monster("IridiumBat")
    assert m.hp == 200
    assert m.damage == 30


def test_unknown_monster_raises():
    with pytest.raises(ValueError):
        Monster("Dragon")


def test_sample_monster_by_depth():
    rng = np.random.default_rng(0)
    for _ in range(20):
        assert sample_monster(depth=10, rng=rng).name == "PurpleSlime"
    sampled = [sample_monster(depth=30, rng=rng).name for _ in range(200)]
    assert set(sampled) <= {"PurpleSlime", "Serpent"}
    sampled = [sample_monster(depth=80, rng=rng).name for _ in range(200)]
    assert set(sampled) <= {"Mummy", "IridiumBat"}


def test_generate_monster_list_size_2_to_6():
    rng = np.random.default_rng(0)
    lst = generate_monster_list(depth=10, rng=rng)
    assert 2 <= len(lst) <= 6


def test_generate_value_returns_nonnegative():
    rng = np.random.default_rng(0)
    m = Monster("PurpleSlime")
    val = m.generate_drop_value(rng)
    assert val >= 0


def test_unknown_depth_zero_raises():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        sample_monster(depth=0, rng=rng)


def test_mummy_revives_50pct_when_no_bomb_used():
    rng = np.random.default_rng(0)
    revives = 0
    for _ in range(2000):
        m = Monster("Mummy")
        m.hp_remaining = 0
        if resolve_mummy_kill(m, bomb_used_this_floor=False, rng=rng):
            revives += 1
    assert 850 < revives < 1150


def test_mummy_does_not_revive_if_bomb_used():
    rng = np.random.default_rng(0)
    for _ in range(100):
        m = Monster("Mummy")
        m.hp_remaining = 0
        revived = resolve_mummy_kill(m, bomb_used_this_floor=True, rng=rng)
        assert not revived
        assert m.permanently_dead


def test_mummy_revives_at_most_once():
    rng = np.random.default_rng(0)
    revived_mummy = None
    for _ in range(50):
        m2 = Monster("Mummy")
        m2.hp_remaining = 0
        if resolve_mummy_kill(m2, bomb_used_this_floor=False, rng=rng):
            revived_mummy = m2
            break
    assert revived_mummy is not None
    assert revived_mummy.revived_once
    revived_mummy.hp_remaining = 0
    revived_again = resolve_mummy_kill(revived_mummy, bomb_used_this_floor=False, rng=rng)
    assert not revived_again
    assert revived_mummy.permanently_dead