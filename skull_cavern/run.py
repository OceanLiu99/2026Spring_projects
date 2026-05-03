"""
SkullCavernRun: orchestrate one in-game day in the Skull Cavern.

Combat is stubbed in this task (always trivially survives)
replaces _maybe_combat() with a real fight.
"""
import numpy as np

from skull_cavern.floor import SkullCavernFloor, ExitResult
from skull_cavern.rock import RockTable
from skull_cavern.time_budget import TimeBudget, ACTION_COSTS
from skull_cavern.economy import net_profit, upfront_cost


class RunResult:
    """Container of summary numbers from one Skull Cavern run."""

    def __init__(self, max_depth, net_profit, gross_revenue, cost, died,
                 time_used, bombs_used, food_used, rocks_broken,
                 monsters_killed, seed, cell_id):
        self.max_depth = max_depth
        self.net_profit = net_profit
        self.gross_revenue = gross_revenue
        self.cost = cost
        self.died = died
        self.time_used = time_used
        self.bombs_used = bombs_used
        self.food_used = food_used
        self.rocks_broken = rocks_broken
        self.monsters_killed = monsters_killed
        self.seed = seed
        self.cell_id = cell_id

    def to_dict(self) -> dict:
        return vars(self).copy()


class SkullCavernRun:
    """
    One Skull Cavern day. Deterministic given (player_config, seed).

    Three Random Number Generators are spawned from the seed to keep mechanics independent.
    - rng_rocks — generates random rock drops/loot
    - rng_monsters — generates random monster encounters
    - rng_combat — generates random combat outcomes
    """

    def __init__(self, player, seed: int):
        self.player = player
        self.seed = seed
        ss = np.random.SeedSequence(seed)
        rocks_seed, monster_seed, combat_seed = ss.spawn(3)
        self.rng_rocks = np.random.default_rng(rocks_seed)
        self.rng_monsters = np.random.default_rng(monster_seed)
        self.rng_combat = np.random.default_rng(combat_seed)
        self.time = TimeBudget()
        self.rock_table = RockTable()
        self.depth = 1
        self.max_depth = 1
        self.gross = 0.0
        self.rocks_broken = 0
        self.monsters_killed = 0
        self.initial_bombs = player.bombs
        self.initial_food = player.food

    def play(self) -> RunResult:
        self.player.reset()
        # Loop until time runs out or player dies, calculate depth
        while not self.time.is_exhausted() and self.player.is_alive():
            floor = SkullCavernFloor(
                depth=self.depth,
                rng=self.rng_rocks,
                luck_value=self.player.luck_value,
            )
            self.populate_floor_monsters(floor)
            exit_result = self.play_floor(floor)
            if exit_result is None:
                break
            descended = self.descend(exit_result)
            self.depth += descended
            if self.depth > self.max_depth:
                self.max_depth = self.depth
        cost = upfront_cost(self.initial_bombs, self.initial_food)
        died = not self.player.is_alive()

        # return a summary of the run results
        return RunResult(
            max_depth=self.max_depth,
            net_profit=net_profit(self.gross, cost, died=died),
            gross_revenue=self.gross,
            cost=cost,
            died=died,
            time_used=1200.0 - self.time.remaining,
            bombs_used=self.initial_bombs - self.player.bombs,
            food_used=self.initial_food - self.player.food,
            rocks_broken=self.rocks_broken,
            monsters_killed=self.monsters_killed,
            seed=self.seed,
            cell_id=self.player.strategy.cell_id(),
        )

    def populate_floor_monsters(self, floor):
        from skull_cavern.monster import generate_monster_list
        floor.monsters = generate_monster_list(floor.depth, self.rng_monsters)

    def play_floor(self, floor):
        """Play through one floor until exit found or time runs out."""
        while floor.rocks_remaining > 0:
            if self.time.is_exhausted() or not self.player.is_alive():
                return None
            if self.player.strategy.bomb.should_use_bomb(self.player.bombs):
                self.time.consume(ACTION_COSTS["place_bomb"])
                self.player.consume_bomb()
                cleared_count = min(6, floor.rocks_remaining)
                exit_result = floor.break_rocks_with_bomb()
                self.collect_rock_drops(cleared_count, floor.depth)
                self.rocks_broken += cleared_count
            else:
                self.time.consume(ACTION_COSTS["pickaxe_swing"]
                                  + ACTION_COSTS["move_per_rock"])
                exit_result = floor.break_rock()
                self.collect_rock_drops(1, floor.depth)
                self.rocks_broken += 1
                self.maybe_combat(floor)
            if exit_result is not None:
                return exit_result
        return None
    
    def descend(self, exit_result) -> int:
        """Descend through the exit, consuming time and returning floors descended."""
        if exit_result.kind == "ladder":
            self.time.consume(ACTION_COSTS["descend_ladder"])
            return 1
        self.time.consume(ACTION_COSTS["descend_shaft"])
        floor_for_shaft_calc = SkullCavernFloor(
            depth=self.depth, rng=self.rng_rocks, luck_value=self.player.luck_value
        )
        return floor_for_shaft_calc.descend_shaft()

    def collect_rock_drops(self, n, depth):
        for _ in range(n):
            item = self.rock_table.sample(depth, self.rng_rocks)
            self.gross += self.rock_table.value_of_drop(item, self.rng_rocks)

    def maybe_combat(self, floor):
        # 5%-per-rock activation + one_round_attack
        from skull_cavern.combat import one_round_attack, COMBAT_ACTIVATION_PROB
        from skull_cavern.monster import resolve_mummy_kill

        live_monsters = []
        for m in floor.monsters:
            if not m.is_dead() and not m.permanently_dead:
                live_monsters.append(m)
        if not live_monsters:
            return
        if self.rng_monsters.random() >= COMBAT_ACTIVATION_PROB:
            return
        idx = int(self.rng_monsters.integers(0, len(live_monsters)))
        target = live_monsters[idx]
        rounds, t, food_eaten = one_round_attack(self.player, target, self.rng_combat)
        self.time.consume(t)
        if target.is_dead():
            if target.name == "Mummy":
                revived = resolve_mummy_kill(target, floor.bomb_used_this_floor,
                                             self.rng_combat)
                if not revived:
                    self.monsters_killed += 1
                    self.gross += target.generate_drop_value(self.rng_monsters)
            else:
                self.monsters_killed += 1
                self.gross += target.generate_drop_value(self.rng_monsters)
        return