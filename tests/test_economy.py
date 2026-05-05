from skull_cavern.economy import (
    PRICE_BOMB, PRICE_FOOD, upfront_cost, net_profit, starting_inventory,
)


def test_prices_match_spec():
    assert PRICE_BOMB == 600
    assert PRICE_FOOD == 175


def test_upfront_cost_for_each_cell():
    assert upfront_cost(bombs=0, food=0) == 0
    assert upfront_cost(bombs=0, food=5) == 875
    assert upfront_cost(bombs=20, food=0) == 12_000
    assert upfront_cost(bombs=20, food=5) == 12_875


def test_net_profit_alive():
    assert net_profit(gross=5000, cost=875, died=False) == 4125


def test_net_profit_on_death_keeps_70_percent():
    assert net_profit(gross=1000, cost=12_000, died=True) == 700 - 1000 - 12_000


def test_starting_inventory_table():
    assert starting_inventory("pickaxe_nofood") == (0, 0)
    assert starting_inventory("pickaxe_food") == (0, 5)
    assert starting_inventory("bomb_nofood") == (20, 0)
    assert starting_inventory("bomb_food") == (20, 5)