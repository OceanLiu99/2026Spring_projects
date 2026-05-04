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


def convergence_rows(n_runs=200):
    """Build convergence rows for max_depth and net_profit.
    Each build gets a separated seed range. The `build_index * 10000` part is
    a simple guard so pickaxe and bomb validation runs do not reuse seeds.

    >>> rows = convergence_rows(n_runs=60)
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
                simple_mock_run,
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


def sensitivity_rows(n_per_value=200):
    """Build sensitivity rows for luck and bomb direction checks.
    Luck is checked with three numeric points, while bombs are checked with
    two boolean points. `value_as_number` inside sensitivity.py maps ‘False/True’
    to 0/1 before the Pearson correlation is calculated.

    >>> rows = sensitivity_rows(n_per_value=10)
    >>> len(rows)
    2
    >>> rows[0]["attr_name"]
    'luck_level'
    """
    rows = []
    base_build = {"cell_id": "bomb_food", "luck_level": 4, "use_bombs": True}

    luck_sweep = sweep_attribute(
        simple_mock_run,
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

    bomb_sweep = sweep_attribute(
        simple_mock_run,
        base_build,
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


def run_phase2_validation(output_dir=None, n_runs=200,
                          sample_n_grid=None, sample_replicates=5,
                          sensitivity_n=200):
    """Run Phase 2 validation and write the four planned CSV files.

    The default output directory is the project `outputs/data` folder. Tests
    pass a smaller output directory and smaller N values so the smoke check is
    fast but still exercises the full pipeline.

    :param output_dir: optional output directory, defaults to outputs/data
    :param n_runs: convergence runs per build and metric
    :param sample_n_grid: optional N grid for sample-size sweep
    :param sample_replicates: number of replicate batches per N
    :param sensitivity_n: runs per sensitivity attribute value
    :return: summary dict with output paths and recommended N

    >>> path = output_data_dir / "_doctest_phase2"
    >>> summary = run_phase2_validation(path, n_runs=60, sample_n_grid=(10, 20), sample_replicates=3, sensitivity_n=10)
    >>> summary["n_final_path"].exists()
    True
    >>> for csv_path in path.glob("*.csv"):
    ...     csv_path.unlink()
    >>> path.rmdir()
    """
    if output_dir is None:
        output_dir = output_data_dir
    output_dir = Path(output_dir)

    if sample_n_grid is None:
        sample_n_grid = (50, 100, 200, 500, 1000)

    # AI-assisted outline: order the driver as convergence -> sample size
    # -> N_final -> sensitivity. I checked the concrete calls and fields.
    # four output tables
    convergence_path = output_dir / "validation_convergence.csv"
    sample_size_path = output_dir / "validation_sample_size.csv"
    sensitivity_path = output_dir / "validation_sensitivity.csv"
    n_final_path = output_dir / "validation_n_final.csv"

    # convergence check
    convergence_result = convergence_rows(n_runs=n_runs)
    write_csv_rows(convergence_path, convergence_result)

    # sample-size check
    sample_build = {"cell_id": "bomb_food", "luck_level": 4, "use_bombs": True}
    sample_result = sweep_n(
        simple_mock_run,
        sample_build,
        "max_depth",
        n_grid=sample_n_grid,
        n_replicates=sample_replicates,
        seed_start=2000000000,
    )
    write_csv_rows(sample_size_path, sample_result)

    recommended_n = recommend_n(sample_result)

    # N_final decision
    if recommended_n is None:
        evidence = "no grid point met target on two adjacent N values"
        n_final = ""
    else:
        evidence = "first N with two adjacent relative CI half-widths under target"
        n_final = recommended_n

    n_final_rows = [{
        "metric": "max_depth",
        "cell_id": sample_build["cell_id"],
        "n_final": n_final,
        "target_relative": 0.05,
        "evidence": evidence,
    }]
    write_csv_rows(n_final_path, n_final_rows)

    # sensitivity check
    sensitivity_result = sensitivity_rows(n_per_value=sensitivity_n)
    write_csv_rows(sensitivity_path, sensitivity_result)

    return {
        "convergence_path": convergence_path,
        "sample_size_path": sample_size_path,
        "sensitivity_path": sensitivity_path,
        "n_final_path": n_final_path,
        "n_final": recommended_n,
    }


def main():
    """Run when called with python -m validation.run_phase2.
    This wrapper keeps command-line behavior separate from the testable
    `run_phase2_validation` function.
    """
    summary = run_phase2_validation()
    print(f"[phase2] N_final recommended = {summary['n_final']}")
    print(f"[phase2] wrote {summary['convergence_path']}")
    print(f"[phase2] wrote {summary['sample_size_path']}")
    print(f"[phase2] wrote {summary['sensitivity_path']}")
    print(f"[phase2] wrote {summary['n_final_path']}")


if __name__ == "__main__":
    main()
