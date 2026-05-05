from skull_cavern.strategy import BombStrategy, FoodStrategy, Strategy


def test_bomb_strategy_uses_bomb_when_inventory_positive():
    s = BombStrategy(use_bombs=True)
    assert s.should_use_bomb(bombs_remaining=5)
    assert not s.should_use_bomb(bombs_remaining=0)


def test_bomb_strategy_off_never_bombs():
    s = BombStrategy(use_bombs=False)
    assert not s.should_use_bomb(bombs_remaining=5)


def test_food_strategy_eats_below_threshold():
    s = FoodStrategy(use_food=True, hp_threshold=0.4)
    assert s.should_eat(hp=20, max_hp=100, food_remaining=3)
    assert not s.should_eat(hp=80, max_hp=100, food_remaining=3)
    assert not s.should_eat(hp=20, max_hp=100, food_remaining=0)


def test_food_strategy_off_never_eats():
    s = FoodStrategy(use_food=False)
    assert not s.should_eat(hp=1, max_hp=100, food_remaining=99)


def test_strategy_bundle_exposes_flags():
    s = Strategy(BombStrategy(True), FoodStrategy(False))
    assert s.uses_bombs() is True
    assert s.uses_food() is False
    assert s.cell_id() == "bomb_nofood"