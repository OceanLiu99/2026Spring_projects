"""Smoke tests for the real experiment runner.
Most Phase 2 validation code uses simple_mock_run so it can be tested before
the full engine is stable. These tests check the real run_cell path: the real
engine output must keep the same required columns and deterministic seed rule.
"""

from experiments.runner import assert_equipment_present
from experiments.runner import run_cell
from validation.contract import key_required


def test_runner_smoke_writes_required_columns():
    df = run_cell(
        experiment_id=99,
        cell_idx=0,
        cell_id="pickaxe_nofood",
        luck_level=4,
        n_runs=3,
    )

    assert len(df) == 3
    for key in key_required:
        assert key in df.columns


def test_runner_seed_determinism():
    df1 = run_cell(99, 0, "pickaxe_nofood", 4, 2)
    df2 = run_cell(99, 0, "pickaxe_nofood", 4, 2)

    assert df1["seed"].tolist() == df2["seed"].tolist()
    #Only check max_depth and net_profit because they are the main metrics used later in analysis.
    assert df1["max_depth"].tolist() == df2["max_depth"].tolist()
    assert df1["net_profit"].tolist() == df2["net_profit"].tolist()


def test_assert_equipment_present_passes():
    assert_equipment_present()
