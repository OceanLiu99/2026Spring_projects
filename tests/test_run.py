from skull_cavern.run import SkullCavernRun, RunResult
from skull_cavern.player import Player
from skull_cavern.strategy import Strategy, BombStrategy, FoodStrategy


def _player(luck=4, bombs=0, food=0, use_bombs=False, use_food=False):
    return Player(
        equipment_names=["Space Boots", "Lava Katana", "", ""],
        skill_level=7,
        luck_level=luck,
        bombs=bombs,
        food=food,
        strategy=Strategy(BombStrategy(use_bombs), FoodStrategy(use_food)),
    )


def test_run_returns_run_result():
    p = _player()
    result = SkullCavernRun(p, seed=1).play()
    assert isinstance(result, RunResult)
    assert result.max_depth >= 1
    assert result.time_used <= 1200.0


def test_deterministic_seed_reproducibility():
    r1 = SkullCavernRun(_player(), seed=42).play()
    r2 = SkullCavernRun(_player(), seed=42).play()
    assert r1.max_depth == r2.max_depth
    assert r1.gross_revenue == r2.gross_revenue
    assert r1.rocks_broken == r2.rocks_broken


def test_different_seeds_produce_different_outcomes():
    r1 = SkullCavernRun(_player(), seed=1).play()
    r2 = SkullCavernRun(_player(), seed=2).play()
    assert (r1.max_depth, r1.rocks_broken, r1.gross_revenue) != \
           (r2.max_depth, r2.rocks_broken, r2.gross_revenue)


def test_higher_luck_descends_deeper_on_average():
    low = [SkullCavernRun(_player(luck=1), seed=s).play().max_depth
           for s in range(50)]
    high = [SkullCavernRun(_player(luck=6), seed=s).play().max_depth
            for s in range(50)]
    assert sum(high) / 50 > sum(low) / 50


def test_bombs_used_iff_strategy_uses_bombs():
    r_no = SkullCavernRun(_player(bombs=0, use_bombs=False), seed=7).play()
    assert r_no.bombs_used == 0
    r_yes = SkullCavernRun(_player(bombs=20, use_bombs=True), seed=7).play()
    assert r_yes.bombs_used > 0


def test_time_budget_conserved():
    r = SkullCavernRun(_player(), seed=10).play()
    assert 0.0 <= r.time_used <= 1200.0


def test_run_result_to_dict_has_all_fields():
    r = SkullCavernRun(_player(), seed=3).play()
    d = r.to_dict()
    assert "max_depth" in d
    assert "net_profit" in d
    assert "seed" in d
    assert "cell_id" in d

def test_deeper_runs_have_higher_death_rate():
    low_luck_deaths = sum(SkullCavernRun(_player(luck=1), seed=s).play().died
                          for s in range(40))
    high_luck_deaths = sum(SkullCavernRun(_player(luck=6), seed=s).play().died
                           for s in range(40))
    assert high_luck_deaths >= low_luck_deaths


def test_food_used_iff_strategy_uses_food():
    r_no = SkullCavernRun(_player(food=0, use_food=False), seed=11).play()
    assert r_no.food_used == 0
    r_yes_total = sum(
        SkullCavernRun(_player(food=5, use_food=True), seed=s).play().food_used
        for s in range(20)
    )
    assert r_yes_total > 0