import numpy as np
from skull_cavern.combat import one_round_attack, COMBAT_ACTIVATION_PROB
from skull_cavern.monster import Monster
from skull_cavern.player import Player
from skull_cavern.strategy import Strategy, BombStrategy, FoodStrategy


def _player(food=0, use_food=False):
    return Player(
        ["Space Boots", "Lava Katana", "", ""], skill_level=7, luck_level=4,
        bombs=0, food=food, strategy=Strategy(BombStrategy(False), FoodStrategy(use_food)),
    )


def test_activation_constant_is_5_percent():
    assert COMBAT_ACTIVATION_PROB == 0.05


def test_player_kills_purple_slime_eventually():
    p = _player()
    m = Monster("PurpleSlime")
    rng = np.random.default_rng(0)
    rounds, time_used, food_eaten = one_round_attack(p, m, rng)
    assert m.is_dead()
    assert p.is_alive()
    assert rounds > 0
    assert time_used == rounds * 0.7


def test_player_dies_to_strong_monster_eventually():
    p = _player()
    p.damage_min = 1
    p.damage_max = 1
    p.defense = 0
    m = Monster("PurpleSlime")
    m.hp_remaining = 10_000
    rng = np.random.default_rng(0)
    one_round_attack(p, m, rng)
    assert not p.is_alive()


def test_food_eaten_when_hp_drops():
    p = _player(food=5, use_food=True)
    p.damage_min = 1
    p.damage_max = 1
    m = Monster("PurpleSlime")
    m.hp_remaining = 1000
    rng = np.random.default_rng(0)
    rounds, time_used, food_eaten = one_round_attack(p, m, rng)
    assert food_eaten >= 1
    assert p.food == 5 - food_eaten