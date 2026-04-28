"""In-game time budget for one Skull Cavern run (1200 minutes = 6 AM to 2 AM)."""

ACTION_COSTS = {
    "pickaxe_swing": 1.0,
    "place_bomb": 4.3,
    "combat_round": 0.7,
    "eat_food": 1.0,
    "descend_ladder": 2.0,
    "descend_shaft": 4.0,
    "move_per_rock": 0.5,
}


class TimeBudget:
    """Tracks remaining in-game minutes for a single Skull Cavern run.

    >>> b = TimeBudget()
    >>> b.consume(100.0)
    >>> b.remaining
    1100.0
    >>> b.is_exhausted()
    False
    """

    def __init__(self, remaining: float = 1200.0):
        self.remaining = remaining

    def consume(self, minutes: float) -> None:
        if minutes < 0:
            raise ValueError(f"cannot consume negative minutes: {minutes}")
        self.remaining = max(0.0, self.remaining - minutes)

    def is_exhausted(self) -> bool:
        return self.remaining <= 0.0
