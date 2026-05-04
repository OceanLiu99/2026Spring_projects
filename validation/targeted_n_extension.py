"""Targeted N extension for design cells whose relative CI half-width
did not stabilize on the standard sample-size grid (50, 100, 200, 500, 1000).
Reruns those cells on an extended grid (1000, 1500, 2000) and writes the
N_final evidence consumed by README §5.
"""

from validation.run_phase2 import cell_uses_bombs
from validation.run_phase2 import output_data_dir
from validation.run_phase2 import write_csv_rows
from validation.sample_size import recommend_n
from validation.sample_size import sweep_n
from validation.simple_mock import simple_mock_run


extension_n_grid = (1000, 1500, 2000)
extension_replicates = 5

targeted_plans = (
    {
        "experiment": "H1",
        "cell_id": "pickaxe_nofood",
        "luck_level": 3,
        "metric": "max_depth",
    },
    {
        "experiment": "H2",
        "cell_id": "bomb_food",
        "luck_level": 4,
        "metric": "net_profit",
    },
    {
        "experiment": "H2",
        "cell_id": "pickaxe_nofood",
        "luck_level": 4,
        "metric": "net_profit",
    },
)


def build_for_plan(plan):
    """Build the engine config dict for one targeted plan.

    :param plan: targeted plan dict
    :return: build dict used by simple_mock_run or real_engine_run

    >>> build_for_plan(targeted_plans[0])["luck_level"]
    3
    >>> build_for_plan(targeted_plans[1])["use_bombs"]
    True
    """
    cell_id = plan["cell_id"]
    return {
        "cell_id": cell_id,
        "luck_level": plan["luck_level"],
        "use_bombs": cell_uses_bombs(cell_id),
    }


def run_targeted_extension(engine, output_dir=None, suffix="_real",
                           n_grid=extension_n_grid,
                           n_replicates=extension_replicates,
                           progress_label="real-extension"):
    """Run the three targeted extension sweeps and write two CSV files.
    Detailed rows keep every N value. Summary rows keep the recommendation for
    each plan, plus an overall row that can be quoted in README if needed.

    :param engine: engine function like real_engine_run(seed, build)
    :param output_dir: optional output directory
    :param suffix: filename suffix
    :param n_grid: extended N grid, default (1000, 1500, 2000)
    :param n_replicates: replicate batches per N
    :param progress_label: optional progress print label
    :return: dict with output paths and overall recommended N

    >>> summary = run_targeted_extension(simple_mock_run, output_dir=output_data_dir / "_doctest_targeted", suffix="_mock", n_grid=(10, 20), n_replicates=2, progress_label=None)
    >>> summary["detail_path"].exists()
    True
    >>> for csv_path in summary["detail_path"].parent.glob("*.csv"):
    ...     csv_path.unlink()
    >>> summary["detail_path"].parent.rmdir()
    """
    if output_dir is None:
        output_dir = output_data_dir

    detail_rows = []
    summary_rows = []
    n_grid = tuple(n_grid)

    # Keep this extension separate so the main Phase 2 driver stays readable.
    for plan_index in range(len(targeted_plans)):
        plan = targeted_plans[plan_index]
        build = build_for_plan(plan)
        plan_rows = []

        for n_index in range(len(n_grid)):
            current_n = n_grid[n_index]
            if progress_label is not None:
                print(
                    f"[targeted:{progress_label}] "
                    f"{plan['experiment']} {plan['cell_id']} "
                    f"luck={plan['luck_level']} {plan['metric']} "
                    f"n={current_n} ({plan_index + 1}/{len(targeted_plans)})"
                )

            sweep_rows = sweep_n(
                engine,
                build,
                plan["metric"],
                n_grid=(current_n,),
                n_replicates=n_replicates,
                seed_start=4000000000 + plan_index * 10000000 + n_index * 1000000,
            )

            for row in sweep_rows:
                current_row = {
                    "experiment": plan["experiment"],
                    "cell_id": plan["cell_id"],
                    "luck_level": plan["luck_level"],
                    "metric": plan["metric"],
                    "n": row["n"],
                    "mean": row["mean"],
                    "std": row["std"],
                    "ci_half_width": row["ci_half_width"],
                    "relative_half_width": row["relative_half_width"],
                    "n_replicates": row["n_replicates"],
                }
                detail_rows.append(current_row)
                plan_rows.append(current_row)

        recommended_n = recommend_n(plan_rows)
        if recommended_n is None:
            selected_n = max(n_grid)
            evidence = "extension grid still did not get two adjacent passing N values"
        else:
            selected_n = recommended_n
            evidence = "two adjacent extension N values met target"

        summary_rows.append({
            "source": "targeted_extension",
            "experiment": plan["experiment"],
            "cell_id": plan["cell_id"],
            "luck_level": plan["luck_level"],
            "metric": plan["metric"],
            "n_final": selected_n,
            "target_relative": 0.05,
            "evidence": evidence,
        })

    overall_n = max(int(row["n_final"]) for row in summary_rows)
    summary_rows.insert(0, {
        "source": "overall_targeted_extension",
        "experiment": "H1_H2",
        "cell_id": "targeted_cells",
        "luck_level": "mixed",
        "metric": "max_depth_and_net_profit",
        "n_final": overall_n,
        "target_relative": 0.05,
        "evidence": "max over targeted extension checks",
    })

    detail_path = output_dir / f"validation_n_extension{suffix}.csv"
    summary_path = output_dir / f"validation_n_extension_summary{suffix}.csv"
    write_csv_rows(detail_path, detail_rows)
    write_csv_rows(summary_path, summary_rows)

    return {
        "detail_path": detail_path,
        "summary_path": summary_path,
        "n_final": overall_n,
    }


def main(engine_name="real"):
    """Run the targeted extension from the command line.

    :param engine_name: "real" or "mock"
    """
    if engine_name == "real":
        from validation.real_engine import real_engine_run
        engine = real_engine_run
        suffix = "_real"
    else:
        engine = simple_mock_run
        suffix = "_mock"

    summary = run_targeted_extension(
        engine,
        suffix=suffix,
        progress_label=engine_name,
    )
    print(f"[targeted:{engine_name}] N extension recommended = {summary['n_final']}")
    print(f"[targeted:{engine_name}] wrote {summary['detail_path']}")
    print(f"[targeted:{engine_name}] wrote {summary['summary_path']}")


if __name__ == "__main__":
    import sys
    engine_name = sys.argv[1] if len(sys.argv) > 1 else "real"
    main(engine_name)
