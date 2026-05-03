"""
Skull Cavern monsters.

Stats (hp, damage, defense, speed) load from sc_monster_stats.csv.
A single Monster class covers all roster entries; identity is the `name` field.
Mummy revive state lives on every instance (only meaningful when name == "Mummy"; harmless otherwise).
"""
from pathlib import Path
import pandas as pd

MONSTER_STATS_PATH = Path(__file__).parent / "data" / "sc_monster_stats.csv"
MONSTER_DROPS_PATH = Path(__file__).parent / "data" / "sc_monster_drop.csv"

_STATS_DF = pd.read_csv(MONSTER_STATS_PATH).set_index("name")
_DROPS_DF = pd.read_csv(MONSTER_DROPS_PATH)


class Monster:
    """One monster instance. Stats come from sc_monster_stats.csv by name."""

    def __init__(self, name: str):
        if name not in _STATS_DF.index:
            raise ValueError(f"unknown monster {name!r}")
        row = _STATS_DF.loc[name]
        self.name = name
        self.hp = int(row["hp"])
        self.damage = int(row["damage"])
        self.defense = int(row["defense"])
        self.speed = int(row["speed"])
        self.hp_remaining = self.hp
        self.active = True
        self.revived_once = False
        self.permanently_dead = False

    def is_dead(self) -> bool:
        return self.hp_remaining <= 0

    def generate_drop_value(self, rng) -> int:
        rows = _DROPS_DF[_DROPS_DF["monster"] == self.name]
        total = 0
        for _, r in rows.iterrows():
            if rng.random() < float(r["drop_rate"]):
                total += int(r["sell_price"])
        return total


def depth_band_names(depth: int):
    if depth < 1:
        raise ValueError(f"depth must be >= 1; got {depth}")
    if depth <= 25:
        return ["PurpleSlime"]
    if depth <= 50:
        return ["PurpleSlime", "Serpent"]
    if depth <= 75:
        return ["Serpent", "Mummy"]
    return ["Mummy", "IridiumBat"]


def sample_monster(depth: int, rng) -> Monster:
    names = depth_band_names(depth)
    name = names[int(rng.integers(0, len(names)))]
    return Monster(name)


def generate_monster_list(depth: int, rng):
    n = int(rng.integers(2, 7))
    return [sample_monster(depth, rng) for _ in range(n)]


def resolve_mummy_kill(mummy: Monster, bomb_used_this_floor: bool, rng) -> bool:
    """A
    pply the Mummy revive rule.

    Returns True if the Mummy revived (came back to full HP).
    Returns False if the Mummy is permanently dead.
    """
    if bomb_used_this_floor or mummy.revived_once:
        mummy.permanently_dead = True
        return False
    if rng.random() < 0.5:
        mummy.revived_once = True
        mummy.hp_remaining = mummy.hp
        return True
    mummy.permanently_dead = True
    return False