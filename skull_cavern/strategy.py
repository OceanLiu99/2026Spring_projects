"""
Player strategy: 
1. binary bomb policy
2. binary food policy
"""


class BombStrategy:
    """Whether the player tries to use a bomb instead of the pickaxe."""

    def __init__(self, use_bombs: bool):
        self.use_bombs = use_bombs

    def should_use_bomb(self, bombs_remaining: int) -> bool:
        """Use a bomb if the strategy is on AND the at least one bomb in inventory.

        >>> BombStrategy(True).should_use_bomb(3)
        True
        >>> BombStrategy(True).should_use_bomb(0)
        False
        """
        return self.use_bombs and bombs_remaining > 0


class FoodStrategy:
    """Whether the player eats food when HP drops below threshold (default 40%, can be changed)."""

    def __init__(self, use_food: bool, hp_threshold: float = 0.4):
        self.use_food = use_food
        self.hp_threshold = hp_threshold

    def should_eat(self, hp: float, max_hp: float, food_remaining: int) -> bool:
        """Eat if strategy is on AND HP fraction < threshold AND at least one food in inventory.

        >>> FoodStrategy(True).should_eat(30, 100, 1)
        True
        >>> FoodStrategy(True).should_eat(50, 100, 1)
        False
        """
        if not self.use_food or food_remaining <= 0:
            return False
        return (hp / max_hp) < self.hp_threshold


class Strategy:
    """A bundle of one bomb policy and one food policy (4 cells total)."""

    def __init__(self, bomb: BombStrategy, food: FoodStrategy):
        self.bomb = bomb
        self.food = food

    def uses_bombs(self) -> bool:
        return self.bomb.use_bombs

    def uses_food(self) -> bool:
        return self.food.use_food

    # what is cell_id for?
    def cell_id(self) -> str:
        b = "bomb" if self.uses_bombs() else "pickaxe"
        f = "food" if self.uses_food() else "nofood"
        return f"{b}_{f}"