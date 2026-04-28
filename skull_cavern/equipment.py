"""
Equipment loader. Refactored from the 2022 Equipment class.

Differences from 2022:
- DB is loaded once at module import, not on every Equipment() call.
- Path is resolved relative to this file, not the working directory.
- Percentage-string handling preserved for backward-compat with 2022 rows.
"""
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "equipments_db.txt"

# Load equipment database
EQUIPMENT_DB = pd.read_csv(DB_PATH, sep=",")


def load_equipment_db() -> pd.DataFrame:
    """Return the cached equipment DataFrame."""
    return EQUIPMENT_DB


def coerce(value, default=0):
    """Convert a DB value to int, treating '10%' as the literal int 10."""
    # problem here: 百分比转为float；最终输出float，否则本身float会被截断
    if isinstance(value, str) and value.endswith("%"):
        try:
            return int(value.rstrip("%"))
        except ValueError:
            return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


class Equipment:
    """Single equipment slot. Reads its row from the EQUIPMENT_DB.

    >>> e = Equipment("Space Boots")
    >>> e.defense
    4
    >>> e.damage_min
    0
    """

    def __init__(self, name: str):
        self.name = name
        df = load_equipment_db()
        # If the equipment is not in the database, set all attributes to 0
        if name not in df["name"].values:
            self.damage_min = 0
            self.damage_max = 0
            self.base_crit_chance = 0.0
            self.crit_chance = 0
            self.crit_power = 0
            self.defense = 0
            self.immunity = 0
            self.luck = 0
            return
            
        # If the equipment is in the database, set the attributes
        row = df[df["name"] == name].iloc[0]
        self.damage_min = coerce(row["damage_min"])
        self.damage_max = coerce(row["damage_max"])
        try:
            self.base_crit_chance = float(row["base_crit_chance"])
        except (TypeError, ValueError):
            self.base_crit_chance = 0.0
        self.crit_chance = coerce(row["crit_chance"])
        self.crit_power = coerce(row["crit_power"])
        self.defense = coerce(row["defense"])
        self.immunity = coerce(row["immunity"])
        self.luck = coerce(row["luck"])
