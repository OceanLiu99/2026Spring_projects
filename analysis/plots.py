"""Plot H1/H2/H3 figures from analysis tables.
It reads outputs/tables and writes the PNG figures used later in README and slides.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analysis.run_analysis import group_rows
from analysis.run_analysis import read_csv_rows
from analysis.run_analysis import require_columns


input_table_dir = Path(__file__).resolve().parent.parent / "outputs" / "tables"
output_figure_dir = Path(__file__).resolve().parent.parent / "outputs" / "figures"

cell_labels = {
    "pickaxe_nofood": "pickaxe + no food",
    "pickaxe_food": "pickaxe + food",
    "bomb_nofood": "bomb + no food",
    "bomb_food": "bomb + food",
}

cell_colors = {
    "pickaxe_nofood": "#4C78A8",
    "pickaxe_food": "#72B7B2",
    "bomb_nofood": "#F58518",
    "bomb_food": "#E45756",
}


def save_figure(fig, output_path):
    """Save one matplotlib figure and close it.

    :param fig: matplotlib figure
    :param output_path: output png path
    :return: output_path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def float_values(rows, column):
    """Collect one numeric column from rows.

    :param rows: list of CSV dict rows
    :param column: column name
    :return: list of float values

    >>> float_values([{"x": "1.5"}, {"x": "2.5"}], "x")
    [1.5, 2.5]
    """
    values = []

    for row in rows:
        values.append(float(row[column]))

    return values


def sample_rows(rows, max_points=2500):
    """Return a deterministic subset for scatter plotting.

    :param rows: list of rows
    :param max_points: maximum rows to return
    :return: sampled rows
    """
    if max_points <= 0:
        raise ValueError("max_points must be positive")
    if len(rows) <= max_points:
        return rows

    step = len(rows) / max_points
    sampled = []

    # deterministic spacing avoids plot-size noise between runs
    for i in range(max_points):
        current_index = int(i * step)
        sampled.append(rows[current_index])

    return sampled


def plot_h1_depth_vs_luck(rows, output_path):
    """Plot H1: depth by luck level and bomb usage.

    :param rows: h1_depth_by_luck rows
    :param output_path: output png path
    :return: output_path
    """
    require_columns(rows, (
        "cell_id",
        "luck_level",
        "mean_depth",
        "ci_low",
        "ci_high",
    ))

    grouped = group_rows(rows, ("cell_id",))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))

    for cell_id in ("pickaxe_nofood", "bomb_nofood"):
        current_key = (cell_id,)
        if current_key not in grouped:
            continue

        current_rows = sorted(grouped[current_key], key=lambda row: int(row["luck_level"]))
        luck_values = float_values(current_rows, "luck_level")
        mean_values = float_values(current_rows, "mean_depth")
        low_values = float_values(current_rows, "ci_low")
        high_values = float_values(current_rows, "ci_high")

        ax.plot(
            luck_values,
            mean_values,
            marker="o",
            linewidth=2,
            color=cell_colors[cell_id],
            label=cell_labels[cell_id],
        )
        ax.fill_between(
            luck_values,
            low_values,
            high_values,
            color=cell_colors[cell_id],
            alpha=0.16,
            linewidth=0,
        )

    ax.set_title("H1: Luck and bombs change expected depth")
    ax.set_xlabel("Luck level")
    ax.set_ylabel("Mean max depth")
    ax.grid(True, linewidth=0.5, alpha=0.35)
    ax.legend(frameon=False)
    return save_figure(fig, output_path)


def plot_h2_profit_cdfs(rows, output_path):
    """Plot H2: empirical net-profit CDFs.

    :param rows: h2_ecdf_points rows
    :param output_path: output png path
    :return: output_path
    """
    require_columns(rows, (
        "cell_id",
        "net_profit",
        "cdf",
    ))

    grouped = group_rows(rows, ("cell_id",))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))

    for cell_id in ("pickaxe_nofood", "pickaxe_food", "bomb_nofood", "bomb_food"):
        current_key = (cell_id,)
        if current_key not in grouped:
            continue

        current_rows = sorted(grouped[current_key], key=lambda row: float(row["net_profit"]))
        profit_values = float_values(current_rows, "net_profit")
        cdf_values = float_values(current_rows, "cdf")
        line_width = 2.4 if cell_id in ("pickaxe_nofood", "bomb_food") else 1.5
        line_alpha = 1.0 if cell_id in ("pickaxe_nofood", "bomb_food") else 0.70

        ax.plot(
            profit_values,
            cdf_values,
            linewidth=line_width,
            alpha=line_alpha,
            color=cell_colors[cell_id],
            label=cell_labels[cell_id],
        )

    ax.axhline(0.75, color="#555555", linewidth=0.8, linestyle="--", alpha=0.45)
    ax.set_title("H2: Net-profit distribution crossing")
    ax.set_xlabel("Net profit")
    ax.set_ylabel("Empirical CDF")
    ax.grid(True, linewidth=0.5, alpha=0.35)
    ax.legend(frameon=False)
    return save_figure(fig, output_path)


def plot_h3_depth_profit_scatter(rows, correlation_rows, output_path):
    """Plot H3: depth against net profit.

    :param rows: h3_scatter_points rows
    :param correlation_rows: h3_correlation rows
    :param output_path: output png path
    :return: output_path
    """
    require_columns(rows, (
        "group",
        "max_depth",
        "net_profit",
    ))
    require_columns(correlation_rows, (
        "group",
        "r",
    ))

    grouped = group_rows(rows, ("group",))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))

    for group_name in ("experiment_1", "experiment_2"):
        current_key = (group_name,)
        if current_key not in grouped:
            continue

        current_rows = sample_rows(grouped[current_key], max_points=1400)
        depth_values = float_values(current_rows, "max_depth")
        profit_values = float_values(current_rows, "net_profit")
        color = "#4C78A8" if group_name == "experiment_1" else "#E45756"

        ax.scatter(
            depth_values,
            profit_values,
            s=8,
            alpha=0.28,
            color=color,
            edgecolors="none",
            label=group_name,
        )

    pooled_r = ""
    for row in correlation_rows:
        if row["group"] == "pooled":
            pooled_r = round(float(row["r"]), 3)

    ax.set_title(f"H3: Depth-profit relationship, pooled r={pooled_r}")
    ax.set_xlabel("Max depth")
    ax.set_ylabel("Net profit")
    ax.grid(True, linewidth=0.5, alpha=0.35)
    ax.legend(frameon=False)
    return save_figure(fig, output_path)


def run_plots(table_dir=None, figure_dir=None):
    """Run all planned analysis plots.

    :param table_dir: optional table directory, defaults to outputs/tables
    :param figure_dir: optional figure directory, defaults to outputs/figures
    :return: summary dict with written figure paths
    """
    if table_dir is None:
        table_dir = input_table_dir
    if figure_dir is None:
        figure_dir = output_figure_dir

    table_dir = Path(table_dir)
    figure_dir = Path(figure_dir)

    h1_rows = read_csv_rows(table_dir / "h1_depth_by_luck.csv")
    h2_rows = read_csv_rows(table_dir / "h2_ecdf_points.csv")
    h3_rows = read_csv_rows(table_dir / "h3_scatter_points.csv")
    h3_correlation_rows = read_csv_rows(table_dir / "h3_correlation.csv")

    # Keep figure output names aligned with the analysis table names.
    output_paths = {
        "h1_depth_vs_luck_path": plot_h1_depth_vs_luck(
            h1_rows,
            figure_dir / "h1_depth_vs_luck.png",
        ),
        "h2_profit_cdfs_path": plot_h2_profit_cdfs(
            h2_rows,
            figure_dir / "h2_profit_cdfs.png",
        ),
        "h3_depth_profit_scatter_path": plot_h3_depth_profit_scatter(
            h3_rows,
            h3_correlation_rows,
            figure_dir / "h3_depth_profit_scatter.png",
        ),
    }

    return output_paths


def main():
    """Run when called with python -m analysis.plots."""
    summary = run_plots()
    for key in sorted(summary.keys()):
        print(f"[plots] wrote {summary[key]}")


if __name__ == "__main__":
    main()
