"""
SkullCavernFloor: per-floor state and the rock-breaking loop.

Exit roll is sourced from https://stardewvalleywiki.com/The_Mines#Ladders
and https://stardewvalleywiki.com/Skull_Cavern :

    P(exit | rock broken) = 0.02 + 0.20 * luck_value + 1 / rocks_remaining
    on exit: P(shaft) = 0.20, else ladder

luck_value: is the daily luck in [-0.10, +0.10]
rocks_remaining: is the rock count *before* the current break/clear

Wiki phrasing for the base + luck: "Every rock destroyed has a base chance
of 2% to spawn a ladder. This is adjusted by daily luck, increasing by 2.5%
at best (0.5% of which is added by the Special Charm) or decreasing by 2%
at worst." We use a uniform 0.20 luck coefficient, matching the wiki minimum
(-0.02 at luck_value = -0.10) and the without-charm best case
(+0.02 at luck_value = +0.10).

The `1 / rocks_remaining` increases the per-rock exit chance as the floorempties
(10 rocks left -> +10%, 4 left -> +25%, etc.).

Right now we don't model the following:
- Ladders spawned by killing monsters.
- Temporary luck buffs (food, Lucky Ring, etc.).
- Special Charm bonus.

Bombs clear up to 6 rocks; the exit roll fires once per bomb. The sparsity bonus
uses the count before clearing.
The last rock on a floor is guaranteed to reveal a ladder.
"""

# Default using bomb, and assume clear 6 rocks per bomb
# (future can add cherry bomb and mega bomb)
BOMB_CLEAR_COUNT = 6

# Exit probability AND luck coefficient constants (from wiki)
EXIT_BASE = 0.02
EXIT_LUCK_COEF = 0.20
SHAFT_PROB = 0.20


class ExitResult:
    """Tag object returned when a rock break reveals an exit."""

    def __init__(self, kind: str):
        if kind not in ("ladder", "shaft"):
            raise ValueError(f"kind must be 'ladder' or 'shaft'; got {kind!r}")
        self.kind = kind

    def __eq__(self, other):
        return isinstance(other, ExitResult) and self.kind == other.kind

    def __repr__(self):
        return f"ExitResult({self.kind!r})"


class SkullCavernFloor:
    """
    One floor's worth of rocks. Monsters list is set externally.

    >>> import numpy as np
    >>> rng = np.random.default_rng(0)
    >>> f = SkullCavernFloor(depth=10, rng=rng, luck_value=0.0)
    >>> 30 <= f.rocks_remaining <= 50
    True
    """

    def __init__(self, depth: int, rng, luck_value: float):
        self.depth = depth
        self.rng = rng
        self.luck_value = luck_value
        self.rocks_remaining = int(rng.integers(30, 51))
        self.bomb_used_this_floor = False
        self.monsters = []

    def exit_probability(self, rocks_before: int) -> float:
        """Per-rock exit probability given the rock count before the break.

        >>> f = SkullCavernFloor(depth=10, rng=np.random.default_rng(0), luck_value=0.0)
        >>> f.exit_probability(10)
        0.02
        """
        return EXIT_BASE + EXIT_LUCK_COEF * self.luck_value + 1.0 / rocks_before

    def roll_exit(self, rocks_before: int):
        if self.rng.random() >= self.exit_probability(rocks_before):
            return None
        if self.rng.random() < SHAFT_PROB:
            return ExitResult("shaft")
        return ExitResult("ladder")

    def break_rock(self, force_no_exit: bool = False):
        """
        Break one rock with the pickaxe.

        - Decrements rocks_remaining by 1.
        - Rolls for exit unless force_no_exit (used by tests). The exit
          roll uses the rock count before the decrement, so the
          sparsity bonus 1/rocks_remaining is well-defined (>=1).
        - If this was the last rock and no exit rolled, returns Ladder
          (guaranteed exit).
        """
        if self.rocks_remaining <= 0:
            return None
        rocks_before = self.rocks_remaining
        self.rocks_remaining -= 1
        if force_no_exit:
            exit_result = None
        else:
            exit_result = self.roll_exit(rocks_before)
        if exit_result is None and self.rocks_remaining == 0:
            return ExitResult("ladder")
        return exit_result

    def break_rocks_with_bomb(self):
        """Clear up to 6 rocks. Roll exit once per bomb (not per rock).

        The sparsity bonus uses the rock count before the bomb clears.
        """
        if self.rocks_remaining <= 0:
            return None
        rocks_before = self.rocks_remaining
        cleared = min(BOMB_CLEAR_COUNT, self.rocks_remaining)
        self.rocks_remaining -= cleared
        self.bomb_used_this_floor = True
        exit_result = self.roll_exit(rocks_before)
        if exit_result is None and self.rocks_remaining == 0:
            return ExitResult("ladder")
        return exit_result

    def descend_shaft(self) -> int:
        """Number of floors descended on a shaft.

        x ~ U{3..8}. With prob 0.10, descend 2x-1; else x.
        """
        x = int(self.rng.integers(3, 9))
        if self.rng.random() < 0.10:
            return 2 * x - 1
        return x