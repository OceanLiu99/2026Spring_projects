"""Phase 2 validation driver: convergence, sample size, and sensitivity.
This file does not add a new statistic. It connects the three validation
modules and writes the small CSV tables used later in README.
"""

import csv
from pathlib import Path

from validation.convergence import assess_engine
from validation.sample_size import recommend_n
from validation.sample_size import sweep_n
from validation.sensitivity import correlation_report
from validation.sensitivity import sweep_attribute
from validation.sensitivity import validate_monotonic
from validation.simple_mock import simple_mock_run


output_data_dir = Path(__file__).resolve().parent.parent / "outputs" / "data"

validation_builds = (
    {"cell_id": "pickaxe_nofood", "luck_level": 4, "use_bombs": False},
    {"cell_id": "pickaxe_food", "luck_level": 4, "use_bombs": False},
    {"cell_id": "bomb_nofood", "luck_level": 4, "use_bombs": True},
    {"cell_id": "bomb_food", "luck_level": 4, "use_bombs": True},
)


def cell_uses_bombs(cell_id):
    """Return whether a strategy cell should carry bombs.

    :param cell_id: strategy cell name
    :return: bool

    >>> cell_uses_bombs("bomb_food")
    True
    >>> cell_uses_bombs("pickaxe_nofood")
    False
    """
    return str(cell_id).startswith("bomb")


def n_final_sample_plans():
    """List the real experiment cells that should influence N_final.
    H1 needs max_depth across all luck x bomb cells. H2 needs net_profit
    across all strategy cells at neutral luck. H3 reuses H1/H2 outputs, so it
    does not get a separate sample-size budget here.

    :return: list of plan dicts

    >>> plans = n_final_sample_plans()
    >>> len(plans)
    16
    >>> plans[0]["experiment"], plans[0]["metric"]
    ('H1', 'max_depth')
    >>> plans[-1]["experiment"], plans[-1]["metric"]
    ('H2', 'net_profit')
    """
    plans = []

    # H1: luck x bomb comparison for max_depth
    for luck_level in (1, 2, 3, 4, 5, 6):
        for cell_id in ("pickaxe_nofood", "bomb_nofood"):
            plans.append({
                "experiment": "H1",
                "cell_id": cell_id,
                "luck_level": luck_level,
                "metric": "max_depth",
                "build": {
                    "cell_id": cell_id,
                    "luck_level": luck_level,
                    "use_bombs": cell_uses_bombs(cell_id),
                },
            })

    # H2: strategy comparison for net_profit at neutral luck
    for cell_id in ("pickaxe_nofood", "pickaxe_food", "bomb_nofood", "bomb_food"):
        plans.append({
            "experiment": "H2",
            "cell_id": cell_id,
            "luck_level": 4,
            "metric": "net_profit",
            "build": {
                "cell_id": cell_id,
                "luck_level": 4,
                "use_bombs": cell_uses_bombs(cell_id),
            },
        })

    return plans


def write_csv_rows(output_path, rows):
    """Write a list of flat dict rows to CSV.
    The first row controls the CSV header order. Keep all rows using the same
    keys, otherwise later rows may lose fields or fail to write.

    :param output_path: csv output path
    :param rows: non-empty list of dict rows
    :return: output_path

    >>> path = output_data_dir / "_doctest_phase2_rows.csv"
    >>> result_path = write_csv_rows(path, [{"name": "demo", "n": 2}])
    >>> result_path.exists()
    True
    >>> path.unlink()
    """
    if len(rows) == 0:
        raise ValueError("rows must not be empty")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def convergence_rows(engine, n_runs=200):
    """Build convergence rows for max_depth and net_profit.
    Each build gets a separated seed range. The `build_index * 10000` part is
    a simple guard so pickaxe and bomb validation runs do not reuse seeds.

    >>> rows = convergence_rows(simple_mock_run, n_runs=60)
    >>> len(rows)
    8
    >>> "final_drift" in rows[0]
    True
    """
    rows = []
    metrics = ("max_depth", "net_profit")

    # collect convergence summaries
    for build_index in range(len(validation_builds)):
        current_build = validation_builds[build_index]

        for metric in metrics:
            summary = assess_engine(
                engine,
                current_build,
                metric,
                n_runs=n_runs,
                seed_start=1000000000 + build_index * 10000,
                window=20,
                min_n=50,
            )
            rows.append({
                "cell_id": current_build["cell_id"],
                "metric": metric,
                "converged": summary["converged"],
                "n_required": summary["n_required"],
                "final_mean": summary["final_mean"],
                "final_drift": summary["final_drift"],
                "n": summary["n"],
                "window": summary["window"],
                "rel_tol": summary["rel_tol"],
                "min_n": summary["min_n"],
            })

    return rows


def sensitivity_rows(engine, n_per_value=200, bomb_sensitivity_mode="use_bombs"):
    """Build sensitivity rows for luck and bomb direction checks.
    Luck is checked with three numeric points. Bomb use is checked by comparing
    either the use_bombs flag (mock engine) or matched cell_id values (real
    engine), because the real engine derives bomb inventory from cell_id.

    >>> rows = sensitivity_rows(simple_mock_run, n_per_value=10)
    >>> len(rows)
    2
    >>> rows[0]["attr_name"]
    'luck_level'
    """
    rows = []
    base_build = {"cell_id": "bomb_food", "luck_level": 4, "use_bombs": True}

    luck_sweep = sweep_attribute(
        engine,
        base_build,
        "luck_level",
        (1, 4, 6),
        "max_depth",
        n_per_value=n_per_value,
        seed_start=3000000000,
    )
    luck_report = correlation_report(luck_sweep)
    luck_monotonic = validate_monotonic(luck_sweep, expected_sign="+")

    rows.append({
        "attr_name": "luck_level",
        "metric": "max_depth",
        "r": luck_report["r"],
        "p_value": luck_report["p_value"],
        "n_points": luck_report["n_points"],
        "expected_sign": "+",
        "monotonic_passed": luck_monotonic["passed"],
    })

    if bomb_sensitivity_mode == "use_bombs":
        bomb_sweep = sweep_attribute(
            engine,
            {"cell_id": "pickaxe_food", "luck_level": 4, "use_bombs": False},
            "use_bombs",
            (False, True),
            "max_depth",
            n_per_value=n_per_value,
            seed_start=3100000000,
        )
        bomb_report = correlation_report(bomb_sweep)
        bomb_monotonic = validate_monotonic(bomb_sweep, expected_sign="+")

        rows.append({
            "attr_name": "use_bombs",
            "metric": "max_depth",
            "r": bomb_report["r"],
            "p_value": bomb_report["p_value"],
            "n_points": bomb_report["n_points"],
            "expected_sign": "+",
            "monotonic_passed": bomb_monotonic["passed"],
        })
        return rows

    if bomb_sensitivity_mode != "cell_id":
        raise ValueError("bomb_sensitivity_mode must be 'use_bombs' or 'cell_id'")

    bomb_sweep = sweep_attribute(
        engine,
        {"cell_id": "pickaxe_food", "luck_level": 4, "use_bombs": False},
        "cell_id",
        ("pickaxe_food", "bomb_food"),
        "max_depth",
        n_per_value=n_per_value,
        seed_start=3100000000,
    )

    bomb_monotonic = validate_monotonic(bomb_sweep, expected_sign="+")
    bomb_rows = bomb_sweep["rows"]
    bomb_delta = bomb_rows[-1]["mean"] - bomb_rows[0]["mean"]
    bomb_passed = bomb_monotonic["passed"] and bomb_delta > 0.0
    if bomb_delta > 0.0:
        bomb_r = 1.0
    elif bomb_delta < 0.0:
        bomb_r = -1.0
    else:
        bomb_r = 0.0

    rows.append({
        "attr_name": "cell_id_bomb_food",
        "metric": "max_depth",
        "r": bomb_r,
        "p_value": None,
        "n_points": 2,
        "expected_sign": "+",
        "monotonic_passed": bomb_passed,
    })

    return rows


def sample_size_rows(engine, n_grid=None, n_replicates=5,
                     target_relative=0.05, progress_label=None):
    """Run sample-size sweeps for every H1/H2 design cell.
    The old draft used only `bomb_food / max_depth`, which could recommend a
    small N that did not represent H1 or H2. This helper keeps the evidence
    tied to the actual experiment cells that will later be rerun.

    :param engine: engine function like simple_mock_run(seed, build)
    :param n_grid: candidate N values
    :param n_replicates: replicate batches per N
    :param target_relative: CI half-width target
    :param progress_label: optional label for progress prints
    :return: (csv rows, decision rows)

    >>> rows, decisions = sample_size_rows(simple_mock_run, n_grid=(10, 20), n_replicates=3)
    >>> len(rows)
    32
    >>> len(decisions)
    16
    >>> rows[0]["experiment"]
    'H1'
    """
    if n_grid is None:
        n_grid = (50, 100, 200, 500, 1000)
    n_grid = tuple(n_grid)

    result_rows = []
    decision_rows = []
    plans = n_final_sample_plans()

    # collect sample-size evidence for each final experiment cell
    for plan_index in range(len(plans)):
        current_plan = plans[plan_index]

        if progress_label is not None:
            print(
                f"[phase2:{progress_label}] sample size "
                f"{current_plan['experiment']} {current_plan['cell_id']} "
                f"luck={current_plan['luck_level']} {current_plan['metric']} "
                f"({plan_index + 1}/{len(plans)})"
            )

        sweep_result = sweep_n(
            engine,
            current_plan["build"],
            current_plan["metric"],
            n_grid=n_grid,
            n_replicates=n_replicates,
            seed_start=2000000000 + plan_index * 1000000,
        )
        recommended_n = recommend_n(
            sweep_result,
            target_relative=target_relative,
        )

        if recommended_n is None:
            selected_n = max(n_grid)
            evidence = "no two adjacent grid points met target; using largest tested N"
        else:
            selected_n = recommended_n
            evidence = "first N with two adjacent relative CI half-widths under target"

        decision_rows.append({
            "source": "sample_size",
            "experiment": current_plan["experiment"],
            "cell_id": current_plan["cell_id"],
            "luck_level": current_plan["luck_level"],
            "metric": current_plan["metric"],
            "n_final": selected_n,
            "target_relative": target_relative,
            "convergence_rel_tol": "",
            "evidence": evidence,
        })

        for sweep_row in sweep_result:
            result_rows.append({
                "experiment": current_plan["experiment"],
                "cell_id": current_plan["cell_id"],
                "luck_level": current_plan["luck_level"],
                "metric": current_plan["metric"],
                "n": sweep_row["n"],
                "mean": sweep_row["mean"],
                "std": sweep_row["std"],
                "ci_half_width": sweep_row["ci_half_width"],
                "relative_half_width": sweep_row["relative_half_width"],
                "n_replicates": sweep_row["n_replicates"],
                "n_recommended": recommended_n if recommended_n is not None else "",
                "target_relative": target_relative,
                "evidence": evidence,
            })

    return result_rows, decision_rows


def n_final_rows(sample_decisions, convergence_result):
    """Combine sample-size and convergence evidence into one N_final table.
    The first row is the overall value to use for H1 and H2. Later rows show
    which sample-size or convergence check pushed the final value upward.

    :param sample_decisions: decision rows returned by sample_size_rows
    :param convergence_result: rows returned by convergence_rows
    :return: (csv rows, overall_n_final)

    >>> sample_decisions = [{"source": "sample_size", "experiment": "H1", "cell_id": "bomb_nofood", "luck_level": 6, "metric": "max_depth", "n_final": 50, "target_relative": 0.05, "convergence_rel_tol": "", "evidence": "demo"}]
    >>> convergence_result = [{"cell_id": "bomb_nofood", "metric": "max_depth", "converged": False, "n_required": None, "n": 200, "rel_tol": 0.01}]
    >>> rows, overall_n = n_final_rows(sample_decisions, convergence_result)
    >>> overall_n
    200
    >>> rows[0]["source"]
    'overall'
    """
    rows = []
    candidate_ns = []

    for decision in sample_decisions:
        current_n = decision["n_final"]
        candidate_ns.append(int(current_n))
        rows.append(decision)

    for convergence_row in convergence_result:
        if convergence_row["converged"] and convergence_row["n_required"] is not None:
            current_n = convergence_row["n_required"]
            evidence = "rolling mean converged by n_required"
        else:
            current_n = convergence_row["n"]
            evidence = "not converged by validation limit; using collected n as guard"

        candidate_ns.append(int(current_n))
        rows.append({
            "source": "convergence",
            "experiment": "phase2",
            "cell_id": convergence_row["cell_id"],
            "luck_level": 4,
            "metric": convergence_row["metric"],
            "n_final": current_n,
            "target_relative": "",
            "convergence_rel_tol": convergence_row["rel_tol"],
            "evidence": evidence,
        })

    overall_n = max(candidate_ns)
    rows.insert(0, {
        "source": "overall",
        "experiment": "H1_H2",
        "cell_id": "all_design_cells",
        "luck_level": "mixed",
        "metric": "max_depth_and_net_profit",
        "n_final": overall_n,
        "target_relative": 0.05,
        "convergence_rel_tol": 0.01,
        "evidence": "max over H1/H2 sample-size decisions and convergence guards",
    })

    return rows, overall_n


def run_phase2_validation(output_dir=None, engine=None, suffix="",
                          n_runs=200, sample_n_grid=None,
                          sample_replicates=5, sensitivity_n=200,
                          progress_label=None,
                          bomb_sensitivity_mode="use_bombs"):
    """Run Phase 2 validation and write the four planned CSV files.
    The default output directory is the project `outputs/data` folder. Tests
    pass a smaller output directory and smaller N values so the smoke check is
    fast but still exercises the full pipeline.

    :param output_dir: optional output directory, defaults to outputs/data
    :param engine: engine function like simple_mock_run(seed, build)
    :param suffix: optional filename suffix, such as "_mock"
    :param n_runs: convergence runs per build and metric
    :param sample_n_grid: optional N grid for sample-size sweep
    :param sample_replicates: number of replicate batches per N
    :param sensitivity_n: runs per sensitivity attribute value
    :param progress_label: optional label for progress prints
    :param bomb_sensitivity_mode: "use_bombs" for mock-like engines or
                                  "cell_id" for real SkullCavernRun
    :return: summary dict with output paths and recommended N

    >>> path = output_data_dir / "_doctest_phase2"
    >>> summary = run_phase2_validation(path, engine=simple_mock_run, n_runs=60, sample_n_grid=(10, 20), sample_replicates=3, sensitivity_n=10)
    >>> summary["n_final_path"].exists()
    True
    >>> for csv_path in path.glob("*.csv"):
    ...     csv_path.unlink()
    >>> path.rmdir()
    """
    if output_dir is None:
        output_dir = output_data_dir
    output_dir = Path(output_dir)

    if engine is None:
        engine = simple_mock_run

    if sample_n_grid is None:
        sample_n_grid = (50, 100, 200, 500, 1000)

    # Keep the driver order aligned with the validation narrative:
    # convergence -> sample size -> N_final -> sensitivity.
    convergence_path = output_dir / f"validation_convergence{suffix}.csv"
    sample_size_path = output_dir / f"validation_sample_size{suffix}.csv"
    sensitivity_path = output_dir / f"validation_sensitivity{suffix}.csv"
    n_final_path = output_dir / f"validation_n_final{suffix}.csv"

    # convergence check
    if progress_label is not None:
        print(f"[phase2:{progress_label}] running convergence")
    convergence_result = convergence_rows(engine, n_runs=n_runs)
    write_csv_rows(convergence_path, convergence_result)

    # sample-size check
    if progress_label is not None:
        print(f"[phase2:{progress_label}] running sample size")
    sample_result, sample_decisions = sample_size_rows(
        engine,
        n_grid=sample_n_grid,
        n_replicates=sample_replicates,
        target_relative=0.05,
        progress_label=progress_label,
    )
    write_csv_rows(sample_size_path, sample_result)

    # N_final decision
    n_final_result, recommended_n = n_final_rows(
        sample_decisions,
        convergence_result,
    )
    write_csv_rows(n_final_path, n_final_result)

    # sensitivity check
    if progress_label is not None:
        print(f"[phase2:{progress_label}] running sensitivity")
    sensitivity_result = sensitivity_rows(
        engine,
        n_per_value=sensitivity_n,
        bomb_sensitivity_mode=bomb_sensitivity_mode,
    )
    write_csv_rows(sensitivity_path, sensitivity_result)

    return {
        "convergence_path": convergence_path,
        "sample_size_path": sample_size_path,
        "sensitivity_path": sensitivity_path,
        "n_final_path": n_final_path,
        "n_final": recommended_n,
    }


def main(engine_name="mock", run_size="default"):
    """Run when called with python -m validation.run_phase2.
    Design different output models to test distinct use cases.
    :param engine_name: "mock" or "real"
    :param run_size: "default", "fast", or "full"
    """
    if engine_name == "real":
        from validation.real_engine import real_engine_run
        engine = real_engine_run
        suffix = ""
        bomb_sensitivity_mode = "cell_id"
    else:
        engine = simple_mock_run
        suffix = "_mock"
        bomb_sensitivity_mode = "use_bombs"

    if engine_name == "real" and run_size == "fast":
        summary = run_phase2_validation(
            engine=engine,
            suffix="_real_fast",
            n_runs=80,
            sample_n_grid=(20, 50),
            sample_replicates=2,
            sensitivity_n=20,
            progress_label="real-fast",
            bomb_sensitivity_mode=bomb_sensitivity_mode,
        )
        print_label = "real-fast"
    else:
        summary = run_phase2_validation(
            engine=engine,
            suffix=suffix,
            progress_label=engine_name,
            bomb_sensitivity_mode=bomb_sensitivity_mode,
        )
        print_label = engine_name

    print(f"[phase2:{print_label}] N_final recommended = {summary['n_final']}")
    print(f"[phase2:{print_label}] wrote {summary['convergence_path']}")
    print(f"[phase2:{print_label}] wrote {summary['sample_size_path']}")
    print(f"[phase2:{print_label}] wrote {summary['sensitivity_path']}")
    print(f"[phase2:{print_label}] wrote {summary['n_final_path']}")


if __name__ == "__main__":
    import sys
    engine_name = sys.argv[1] if len(sys.argv) > 1 else "mock"
    run_size = sys.argv[2] if len(sys.argv) > 2 else "default"
    main(engine_name, run_size)

