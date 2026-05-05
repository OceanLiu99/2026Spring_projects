from skull_cavern.equipment import Equipment, load_equipment_db


def test_load_returns_dataframe_with_expected_columns():
    df = load_equipment_db()
    assert {"name", "damage_min", "damage_max", "defense", "luck"}.issubset(df.columns)


def test_space_boots_present_with_defense_4():
    e = Equipment("Space Boots")
    assert e.defense == 4
    assert e.damage_max == 0


def test_lava_katana_damage_range():
    e = Equipment("Lava Katana")
    assert e.damage_min == 55
    assert e.damage_max == 64
    assert e.crit_power == 10


def test_unknown_equipment_returns_zeros():
    e = Equipment("NoSuchItem")
    assert e.defense == 0
    assert e.damage_min == 0

def test_percentage_crit_chance():
    e = Equipment("Jade Ring")
    assert e.crit_power == 0.10
