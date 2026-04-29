"""
Player class for Skull Cavern. Refactored from the 2022 Player class.

Differences from 2022 Player:
- HP is an instance field (not class field), so multiple players in one process don't share state.
- Luck is a discrete level 1-6 mapped to a representative midpoint.
- Inventory (bombs, food) and strategy are first-class fields.
- Equipment aggregation produces explicit, named attributes.
"""
from skull_cavern.equipment import Equipment

# simulate the luck value for 6 luck levels
LUCK_VALUES = {
    1: -0.10,
    2: -0.085,
    3: -0.035,
    4: 0.035,
    5: 0.085,
    6: 0.10,
}

FOOD_HEAL = 115  # assum Spicy Eel first, future update to more food (maybe a new food class)


class Player:
    """
    Skull Cavern player stats including equipment, luck, inventory, and strategy.

    >>> from skull_cavern.strategy import Strategy, BombStrategy, FoodStrategy
    >>> s = Strategy(BombStrategy(False), FoodStrategy(False))
    >>> p = Player(["", "", "", ""], skill_level=7, luck_level=4, bombs=0, food=0, strategy=s)
    >>> p.hp
    100
    >>> p.is_alive()
    True
    """

    def __init__(self, equipment_names, skill_level, luck_level, bombs, food, strategy, max_hp=100):
        # check if the luck level is valid
        if luck_level not in LUCK_VALUES:
            raise ValueError(
                f"luck_level must be in {sorted(LUCK_VALUES)}; got {luck_level}"
            )
        self.equipment_names = equipment_names
        self.skill_level = skill_level
        self.luck_level = luck_level
        self.luck_value = LUCK_VALUES[luck_level]
        self.initial_bombs = bombs
        self.initial_food = food
        self.bombs = bombs
        self.food = food
        self.strategy = strategy
        self.max_hp = max_hp
        self.hp = max_hp
        self.aggregate_equipment()

    def aggregate_equipment(self):
        dmin = 0
        dmax = 0
        defense = 0
        base_crit = 0.0
        crit_chance = 0
        crit_power = 0
        for name in self.equipment_names:
            # skip empty equipment names
            if not name:
                continue
            e = Equipment(name)
            # aggregate the equipment stats
            dmin += e.damage_min
            dmax += e.damage_max
            defense += e.defense
            base_crit += e.base_crit_chance
            crit_chance += e.crit_chance
            crit_power += e.crit_power
        self.damage_min = dmin
        self.damage_max = dmax
        self.defense = defense
        self.base_crit_chance = base_crit
        self.crit_chance = crit_chance
        self.crit_power = crit_power

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, n: float) -> None:
        self.hp -= n

    def eat_food(self) -> None:
        if self.food <= 0:
            raise ValueError("no food in inventory")
        self.hp = min(self.max_hp, self.hp + FOOD_HEAL)
        self.food -= 1

    def consume_bomb(self) -> None:
        if self.bombs <= 0:
            raise ValueError("no bombs in inventory")
        self.bombs -= 1

    def reset(self) -> None:
        self.hp = self.max_hp
        self.bombs = self.initial_bombs
        self.food = self.initial_food