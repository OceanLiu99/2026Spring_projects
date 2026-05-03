"""Combat: turn-exchange between the player and one monster."""

from skull_cavern.time_budget import ACTION_COSTS

COMBAT_ACTIVATION_PROB = 0.05


def one_round_attack(player, monster, rng) -> tuple[int, float, int]:
    """Run a complete fight until the monster dies or the player dies.

    total_damage_player = player_damage - monster.defense + crit_bonus
    total_damage_monster = monster.damage - player.defense

    Both are at least 1.0.
    crit_bonus = (3 + crit_power)/50 when crit fires.
    Food is consumed mid-combat per FoodStrategy when HP < threshold.
    """
    rounds = 0
    food_eaten = 0
    base_crit = float(player.base_crit_chance) + 0.02 * int(player.crit_chance)
    if base_crit < 0.0:
        base_crit = 0.0
    if base_crit > 1.0:
        base_crit = 1.0
    while not monster.is_dead() and player.is_alive():
        rounds += 1
        damage_roll = int(rng.integers(int(player.damage_min),
                                       int(player.damage_max) + 1))
        crit_bonus = 0.0
        if rng.random() < base_crit:
            crit_bonus = (3 + player.crit_power) / 50.0
        dmg_to_monster = damage_roll - monster.defense + crit_bonus
        if dmg_to_monster < 1.0:
            dmg_to_monster = 1.0
        monster.hp_remaining -= dmg_to_monster
        if monster.is_dead():
            break
        dmg_to_player = monster.damage - player.defense
        if dmg_to_player < 1.0:
            dmg_to_player = 1.0
        player.take_damage(dmg_to_player)
        if player.strategy.food.should_eat(player.hp, player.max_hp, player.food):
            player.eat_food()
            food_eaten += 1
    time_used = rounds * ACTION_COSTS["combat_round"]
    if food_eaten:
        time_used += food_eaten * ACTION_COSTS["eat_food"]
    return rounds, time_used, food_eaten