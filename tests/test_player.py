import pytest
from skull_cavern.player import Player, LUCK_VALUES
from skull_cavern.strategy import Strategy, BombStrategy, FoodStrategy


def strategy(bombs=False, food=False):
    return Strategy(BombStrategy(bombs), FoodStrategy(food))


def test_default_player_has_full_hp_and_no_inventory():
    p = Player(equipment_names=["Space Boots", "Lava Katana", "", ""],
               skill_level=7, luck_level=4, bombs=0, food=0,
               strategy=strategy())
    assert p.hp == p.max_hp == 100
    assert p.bombs == 0
    assert p.is_alive()
    assert p.luck_value == LUCK_VALUES[4]


def test_take_damage_kills_below_zero():
    p = Player(equipment_names=["", "", "", ""], skill_level=0, luck_level=4,
               bombs=0, food=0, strategy=strategy())
    p.take_damage(150)
    assert not p.is_alive()
    assert p.hp <= 0


def test_eat_food_restores_hp_and_decrements():
    p = Player(equipment_names=["", "", "", ""], skill_level=0, luck_level=4,
               bombs=0, food=3, strategy=strategy(food=True))
    p.take_damage(80)
    assert p.hp == 20
    p.eat_food()
    assert p.hp == p.max_hp
    assert p.food == 2


def test_consume_bomb_decrements_or_raises():
    p = Player(equipment_names=["", "", "", ""], skill_level=0, luck_level=4,
               bombs=2, food=0, strategy=strategy(bombs=True))
    p.consume_bomb()
    assert p.bombs == 1
    p.consume_bomb()
    assert p.bombs == 0
    with pytest.raises(ValueError):
        p.consume_bomb()


def test_attribute_aggregation_from_equipment():
    p = Player(equipment_names=["Space Boots", "Lava Katana", "", ""],
               skill_level=7, luck_level=4, bombs=0, food=0,
               strategy=strategy())
    assert p.damage_min == 55
    assert p.damage_max == 64
    assert p.defense == 4


def test_invalid_luck_level_raises():
    with pytest.raises(ValueError):
        Player(equipment_names=["", "", "", ""], skill_level=0, luck_level=0,
               bombs=0, food=0, strategy=strategy())


def test_reset_restores_hp_and_inventory():
    p = Player(equipment_names=["", "", "", ""], skill_level=0, luck_level=4,
               bombs=5, food=3, strategy=strategy(bombs=True, food=True))
    p.take_damage(50)
    p.consume_bomb()
    p.eat_food()
    p.reset()
    assert p.hp == p.max_hp
    assert p.bombs == 5
    assert p.food == 3
    assert p.is_alive()