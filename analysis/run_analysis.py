"""Run H1/H2/H3 analysis tables from existing experiment CSVs.
It reads outputs/data and writes small, separate tables used later in plots.
"""

import csv
from pathlib import Path

from analysis.stats import cohen_d
from analysis.stats import mean_ci_95
from analysis.stats import pearson_with_ci
from analysis.stats import welch_t
from validation.sample_size import mean_value
from validation.sample_size import std_value


input_data_dir = Path(__file__).resolve().parent.parent / "outputs" / "data"
output_table_dir = Path(__file__).resolve().parent.parent / "outputs" / "tables"

required_result_columns = (
    "max_depth",
    "net_profit",
    "died",
    "seed",
    "cell_id",
    "luck_level",
    "experiment_id",
)

plot_quantiles = (
    0.0, 0.05, 0.10, 0.15, 0.20,
    0.25, 0.30, 0.35, 0.40, 0.45,
    0.50, 0.55, 0.60, 0.65, 0.70,
    0.75, 0.80, 0.85, 0.90, 0.95, 1.0,
)


def read_csv_rows(input_path):
    """Read CSV rows as dictionaries.

    :param input_path: input csv path
    :return: list of dict rows
    """
    with Path(input_path).open(newline="", encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


def write_csv_rows(output_path, rows):
    """Write a list of flat dict rows to CSV.

    :param output_path: output csv path
    :param rows: non-empty list of dict rows
    :return: output_path

    >>> path = output_table_dir / "_doctest_analysis_rows.csv"
    >>> result_path = write_csv_rows(path, [{"name": "demo", "n": 2}])
    >>> result_path.exists()
    True
    >>> path.unlink()
    """
    if len(rows) == 0:
        raise ValueError("rows must not be empty")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())

    with Path(output_path).open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def require_columns(rows, required_columns):
    """Check that loaded CSV rows contain the needed columns.

    :param rows: list of CSV dict rows
    :param required_columns: required column names

    >>> require_columns([{"a": "1", "b": "2"}], ("a",))
    """
    if len(rows) == 0:
        raise ValueError("rows must not be empty")

    missing_columns = []
    for column in required_columns:
        if column not in rows[0]:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"missing required columns: {missing_columns}")


def group_rows(rows, group_columns):
    """Group rows by one or more columns.

    :param rows: list of CSV dict rows
    :param group_columns: columns used as group key
    :return: dict from tuple key to row list

    >>> grouped = group_rows([{"cell_id": "a"}, {"cell_id": "a"}], ("cell_id",))
    >>> len(grouped[("a",)])
    2
    """
    grouped = {}

    # collect rows by group key
    for row in rows:
        current_key = tuple(row[column] for column in group_columns)
        if current_key not in grouped:
            grouped[current_key] = []
        grouped[current_key].append(row)

    return grouped


def metric_values(rows, metric):
    """Collect one numeric metric from rows.

    :param rows: list of CSV dict rows
    :param metric: metric column name
    :return: list of float values

    >>> metric_values([{"max_depth": "10"}, {"max_depth": "20"}], "max_depth")
    [10.0, 20.0]
    """
    values = []

    for row in rows:
        values.append(float(row[metric]))

    return values


def died_rate(rows):
    """Calculate the died fraction in a group.

    :param rows: list of CSV dict rows
    :return: float died rate

    >>> died_rate([{"died": "True"}, {"died": "False"}])
    0.5
    """
    if len(rows) == 0:
        raise ValueError("rows must not be empty")

    died_count = 0
    for row in rows:
        if str(row["died"]).lower() == "true":
            died_count += 1

    return died_count / len(rows)


def quantile_value(samples, quantile):
    """Return a linearly interpolated sample quantile.

    :param samples: list of numeric samples
    :param quantile: value between 0 and 1
    :return: float quantile value

    >>> quantile_value([10, 20, 30], 0.5)
    20.0
    """
    if len(samples) == 0:
        raise ValueError("samples must not be empty")
    if quantile < 0 or quantile > 1:
        raise ValueError("quantile must be between 0 and 1")

    sorted_values = sorted(float(value) for value in samples)
    if len(sorted_values) == 1:
        return sorted_values[0]

    position = quantile * (len(sorted_values) - 1)
    low_index = int(position)
    high_index = min(low_index + 1, len(sorted_values) - 1)
    weight = position - low_index

    low_value = sorted_values[low_index]
    high_value = sorted_values[high_index]
    return low_value + (high_value - low_value) * weight


def mean_summary_row(hypothesis, cell_id, luck_level, metric_name, output_name, samples):
    """Build one mean + CI row for line or bar plots.

    :param hypothesis: H1 or H2
    :param cell_id: strategy cell id
    :param luck_level: luck level value
    :param metric_name: source metric name
    :param output_name: output mean column stem
    :param samples: list of numeric samples
    :return: flat dict row
    """
    current_mean, low, high = mean_ci_95(samples)

    return {
        "hypothesis": hypothesis,
        "cell_id": cell_id,
        "luck_level": luck_level,
        "metric": metric_name,
        "n": len(samples),
        f"mean_{output_name}": current_mean,
        f"std_{output_name}": std_value(samples),
        "ci_low": low,
        "ci_high": high,
    }


def effect_row(effect_name, metric_name, base_cell, comparison_cell,
               base_luck, comparison_luck, base_samples, comparison_samples):
    """Build one effect-comparison row.

    :param effect_name: short effect label
    :param metric_name: source metric name
    :param base_cell: baseline cell id
    :param comparison_cell: comparison cell id
    :param base_luck: baseline luck level
    :param comparison_luck: comparison luck level
    :param base_samples: baseline samples
    :param comparison_samples: comparison samples
    :return: flat dict row
    """
    base_mean = mean_value(base_samples)
    comparison_mean = mean_value(comparison_samples)
    t_stat, p_value = welch_t(comparison_samples, base_samples)
    effect_size = cohen_d(comparison_samples, base_samples)

    return {
        "effect_name": effect_name,
        "metric": metric_name,
        "base_cell": base_cell,
        "comparison_cell": comparison_cell,
        "base_luck": base_luck,
        "comparison_luck": comparison_luck,
        "n_base": len(base_samples),
        "n_comparison": len(comparison_samples),
        "base_mean": base_mean,
        "comparison_mean": comparison_mean,
        "mean_gain": comparison_mean - base_mean,
        "t_stat": t_stat,
        "p_value": p_value,
        "cohen_d": effect_size,
    }


def build_h1_depth_by_luck_rows(rows):
    """Build H1 line-plot table for depth by luck.

    :param rows: H1 CSV rows
    :return: list of flat rows
    """
    require_columns(rows, required_result_columns)
    result_rows = []
    grouped = group_rows(rows, ("cell_id", "luck_level"))

    # one row per plotted point
    for key in sorted(grouped.keys(), key=lambda item: (item[0], int(item[1]))):
        cell_id, luck_level = key
        samples = metric_values(grouped[key], "max_depth")
        result_rows.append(mean_summary_row(
            "H1",
            cell_id,
            luck_level,
            "max_depth",
            "depth",
            samples,
        ))

    return result_rows


def build_h1_effect_summary_rows(rows):
    """Build H1 formal luck-vs-bomb effect summary.

    :param rows: H1 CSV rows
    :return: list of flat rows
    """
    require_columns(rows, required_result_columns)
    grouped = group_rows(rows, ("cell_id", "luck_level"))

    # These two comparisons match H1: luck swing first, bomb switch second.
    luck_low_key = ("pickaxe_nofood", "1")
    luck_high_key = ("pickaxe_nofood", "6")
    bomb_base_key = ("pickaxe_nofood", "4")
    bomb_on_key = ("bomb_nofood", "4")

    for key in (luck_low_key, luck_high_key, bomb_base_key, bomb_on_key):
        if key not in grouped:
            raise ValueError(f"missing H1 group: {key}")

    luck_effect = effect_row(
        "luck_1_to_6_bombs_off",
        "max_depth",
        luck_low_key[0],
        luck_high_key[0],
        luck_low_key[1],
        luck_high_key[1],
        metric_values(grouped[luck_low_key], "max_depth"),
        metric_values(grouped[luck_high_key], "max_depth"),
    )
    bomb_effect = effect_row(
        "bomb_on_at_luck_4",
        "max_depth",
        bomb_base_key[0],
        bomb_on_key[0],
        bomb_base_key[1],
        bomb_on_key[1],
        metric_values(grouped[bomb_base_key], "max_depth"),
        metric_values(grouped[bomb_on_key], "max_depth"),
    )

    hypothesis_passed = luck_effect["mean_gain"] > bomb_effect["mean_gain"]
    luck_effect["luck_gain_exceeds_bomb_gain"] = hypothesis_passed
    bomb_effect["luck_gain_exceeds_bomb_gain"] = hypothesis_passed

    return [luck_effect, bomb_effect]


def build_h2_profit_summary_rows(rows):
    """Build H2 profit summary rows by strategy cell.

    :param rows: H2 CSV rows
    :return: list of flat rows
    """
    require_columns(rows, required_result_columns)
    result_rows = []
    grouped = group_rows(rows, ("cell_id",))
    cell_order = ("pickaxe_nofood", "pickaxe_food", "bomb_nofood", "bomb_food")

    # one row per strategy cell
    for cell_id in cell_order:
        current_key = (cell_id,)
        if current_key in grouped:
            current_rows = grouped[current_key]
            samples = metric_values(current_rows, "net_profit")
            current_mean, low, high = mean_ci_95(samples)
            result_rows.append({
                "hypothesis": "H2",
                "cell_id": cell_id,
                "metric": "net_profit",
                "n": len(samples),
                "mean_profit": current_mean,
                "std_profit": std_value(samples),
                "ci_low": low,
                "ci_high": high,
                "q10": quantile_value(samples, 0.10),
                "q25": quantile_value(samples, 0.25),
                "q50": quantile_value(samples, 0.50),
                "q75": quantile_value(samples, 0.75),
                "q90": quantile_value(samples, 0.90),
                "died_rate": died_rate(current_rows),
            })

    return result_rows


def build_h2_quantile_crossing_rows(rows):
    """Build H2 crossing rows for bomb+food vs pickaxe+no-food.

    :param rows: H2 CSV rows
    :return: list of flat rows
    """
    require_columns(rows, required_result_columns)
    grouped = group_rows(rows, ("cell_id",))
    pickaxe_key = ("pickaxe_nofood",)
    bomb_food_key = ("bomb_food",)

    if pickaxe_key not in grouped or bomb_food_key not in grouped:
        raise ValueError("H2 crossing needs pickaxe_nofood and bomb_food")

    pickaxe_samples = metric_values(grouped[pickaxe_key], "net_profit")
    bomb_food_samples = metric_values(grouped[bomb_food_key], "net_profit")
    result_rows = []

    # Quantile rows make the lower-tail and upper-tail crossing easy to read.
    for quantile in plot_quantiles:
        pickaxe_profit = quantile_value(pickaxe_samples, quantile)
        bomb_food_profit = quantile_value(bomb_food_samples, quantile)
        result_rows.append({
            "hypothesis": "H2",
            "metric": "net_profit",
            "quantile": quantile,
            "pickaxe_nofood_profit": pickaxe_profit,
            "bomb_food_profit": bomb_food_profit,
            "bomb_minus_pickaxe": bomb_food_profit - pickaxe_profit,
            "bomb_food_higher": bomb_food_profit > pickaxe_profit,
        })

    return result_rows


def build_h2_ecdf_rows(rows):
    """Build full H2 empirical CDF points for later CDF plots.

    :param rows: H2 CSV rows
    :return: list of flat rows
    """
    require_columns(rows, required_result_columns)
    result_rows = []
    grouped = group_rows(rows, ("cell_id",))

    for cell_key in sorted(grouped.keys()):
        cell_id = cell_key[0]
        samples = sorted(metric_values(grouped[cell_key], "net_profit"))
        sample_count = len(samples)

        for i in range(sample_count):
            result_rows.append({
                "hypothesis": "H2",
                "cell_id": cell_id,
                "metric": "net_profit",
                "rank": i + 1,
                "n": sample_count,
                "net_profit": samples[i],
                "cdf": (i + 1) / sample_count,
            })

    return result_rows


def build_h3_correlation_rows(rows):
    """Build H3 depth-profit correlation rows.

    :param rows: pooled H3 CSV rows
    :return: list of flat rows
    """
    require_columns(rows, required_result_columns)
    result_rows = []
    grouped = group_rows(rows, ("experiment_id",))

    # Show the pooled H3 relationship first, then split by source experiment.
    # The split view helps reveal whether H1 or H2 is driving the pooled result.
    group_list = [("pooled", rows)]

    for experiment_id in sorted(grouped.keys(), key=lambda item: int(item[0])):
        group_list.append((f"experiment_{experiment_id[0]}", grouped[experiment_id]))

    # correlation by pooled and source experiment group
    for group_name, current_rows in group_list:
        depth_values = metric_values(current_rows, "max_depth")
        profit_values = metric_values(current_rows, "net_profit")
        r_value, low, high, p_value = pearson_with_ci(depth_values, profit_values)
        result_rows.append({
            "hypothesis": "H3",
            "group": group_name,
            "metric_x": "max_depth",
            "metric_y": "net_profit",
            "n": len(depth_values),
            "r": r_value,
            "r_low": low,
            "r_high": high,
            "p_value": p_value,
            "threshold": 0.6,
            "hypothesis_passed": r_value > 0.6,
        })

    return result_rows


def build_h3_scatter_rows(rows):
    """Build H3 scatter points for later plots.

    :param rows: pooled H3 CSV rows
    :return: list of flat rows
    """
    require_columns(rows, required_result_columns)
    result_rows = []

    for row in rows:
        result_rows.append({
            "hypothesis": "H3",
            "group": f"experiment_{row['experiment_id']}",
            "seed": row["seed"],
            "cell_id": row["cell_id"],
            "luck_level": row["luck_level"],
            "experiment_id": row["experiment_id"],
            "max_depth": float(row["max_depth"]),
            "net_profit": float(row["net_profit"]),
        })

    return result_rows


def run_analysis(data_dir=None, table_dir=None):
    """Run analysis tables for H1, H2, and H3.

    :param data_dir: optional inputs directory, defaults to outputs/data
    :param table_dir: optional table directory, defaults to outputs/tables
    :return: summary dict with written table paths
    """
    if data_dir is None:
        data_dir = input_data_dir
    if table_dir is None:
        table_dir = output_table_dir

    data_dir = Path(data_dir)
    table_dir = Path(table_dir)

    h1_rows = read_csv_rows(data_dir / "h1_luck_vs_bomb.csv")
    h2_rows = read_csv_rows(data_dir / "h2_profit_distributions.csv")
    h3_rows = read_csv_rows(data_dir / "h3_pooled.csv")

    # Keep output paths in one place so filenames and return keys stay aligned.
    output_paths = {
        "h1_depth_by_luck_path": write_csv_rows(
            table_dir / "h1_depth_by_luck.csv",
            build_h1_depth_by_luck_rows(h1_rows),
        ),
        "h1_effect_summary_path": write_csv_rows(
            table_dir / "h1_effect_summary.csv",
            build_h1_effect_summary_rows(h1_rows),
        ),
        "h2_profit_summary_path": write_csv_rows(
            table_dir / "h2_profit_summary.csv",
            build_h2_profit_summary_rows(h2_rows),
        ),
        "h2_quantile_crossing_path": write_csv_rows(
            table_dir / "h2_quantile_crossing.csv",
            build_h2_quantile_crossing_rows(h2_rows),
        ),
        "h2_ecdf_points_path": write_csv_rows(
            table_dir / "h2_ecdf_points.csv",
            build_h2_ecdf_rows(h2_rows),
        ),
        "h3_correlation_path": write_csv_rows(
            table_dir / "h3_correlation.csv",
            build_h3_correlation_rows(h3_rows),
        ),
        "h3_scatter_points_path": write_csv_rows(
            table_dir / "h3_scatter_points.csv",
            build_h3_scatter_rows(h3_rows),
        ),
    }

    return output_paths


def main():
    """Run when called with python -m analysis.run_analysis."""
    summary = run_analysis()
    for key in sorted(summary.keys()):
        print(f"[analysis] wrote {summary[key]}")


if __name__ == "__main__":
    main()
