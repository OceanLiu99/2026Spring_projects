"""Sample-size sweep and N_final recommendation for Phase 2 validation."""

import math
import statistics

from validation.contract import result_dict_check

try:
    from scipy import stats
except ImportError:
    stats = None


default_n_grid = (50, 100, 200, 500, 1000)
default_target_relative = 0.05
default_n_replicates = 5


def mean_value(samples):
    """Calculate sample mean.

    :param samples: list of numeric samples
    :return: float sample mean

    >>> mean_value([1, 2, 3])
    2.0
    """
    if len(samples) == 0:
        raise ValueError("samples must not be empty")

    current_total = 0.0
    for value in samples:
        current_total += float(value)
    return current_total / len(samples)


def std_value(samples):
    """Calculate sample standard deviation.

    :param samples: list of numeric samples
    :return: float sample standard deviation

    >>> round(std_value([1, 2, 3]), 3)
    1.0
    """
    if len(samples) < 2:
        raise ValueError("at least two samples are required")

    return float(statistics.stdev(samples))


def t_critical_value(degrees_freedom, level=0.95):
    """Return a t critical value for the requested confidence level.

    :param degrees_freedom: n - 1
    :param level: confidence level
    :return: critical value

    >>> round(t_critical_value(4), 3)
    2.776
    """
    if degrees_freedom <= 0:
        raise ValueError("degrees_freedom must be positive")
    if level <= 0 or level >= 1:
        raise ValueError("level must be between 0 and 1")

    # ***AI-assisted draft***: use the t distribution formula, then I checked the CI math.
    alpha = 1.0 - level
    if stats is not None:
        return float(stats.t.ppf(1.0 - alpha / 2.0, degrees_freedom))

    # fallback for local venvs where scipy is not installed yet
    if level != 0.95:
        raise ValueError("fallback table only supports 0.95 confidence level")

    t_table_95 = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
        11: 2.201,
        12: 2.179,
        13: 2.160,
        14: 2.145,
        15: 2.131,
        16: 2.120,
        17: 2.110,
        18: 2.101,
        19: 2.093,
        20: 2.086,
        21: 2.080,
        22: 2.074,
        23: 2.069,
        24: 2.064,
        25: 2.060,
        26: 2.056,
        27: 2.052,
        28: 2.048,
        29: 2.045,
        30: 2.042,
    }

    if degrees_freedom in t_table_95:
        return t_table_95[degrees_freedom]

    return 1.96


def ci_half_width(samples, level=0.95):
    """Analytic t-based 95% CI half-width on the sample mean.

    :param samples: list of numeric samples (n >= 2)
    :param level: confidence level, default 0.95
    :return: float CI half-width
    :raises ValueError: if len(samples) < 2

    >>> round(ci_half_width([1.0, 2.0, 3.0, 4.0, 5.0]), 3)
    1.963
    """
    if len(samples) < 2:
        raise ValueError("at least two samples are required")

    current_std = std_value(samples)
    critical_value = t_critical_value(len(samples) - 1, level=level)
    return critical_value * current_std / math.sqrt(len(samples))


def sweep_n(engine, build, metric,n_grid=default_n_grid,
            n_replicates=default_n_replicates,seed_start=2000000000):
    """For each N in n_grid, run n_replicates independent batches.

    Each batch uses non-overlapping seed segments. Records mean, std,
    ci_half_width, relative_half_width across replicates.Use absolutely
    large seed values to avoid collisions during the sweep.

    :return: list of dicts, one per N, with keys
             {n, mean, std, ci_half_width, relative_half_width, n_replicates}
    """
    if n_replicates < 2:
        raise ValueError("n_replicates must be at least 2")

    result_rows = []
    seed_offset = 0

    # sweep N values
    for current_n in n_grid:
        if current_n <= 0:
            raise ValueError("n_grid values must be positive")

        batch_mean_list = []

        # collect replicate batches
        for replicate_index in range(n_replicates):
            sample_list = []

            for i in range(current_n):
                # AI helped sketch the non-overlapping seed batches, I kept it explicit for review.
                current_seed = seed_start + seed_offset
                seed_offset += 1

                current_build = build.copy()
                result_row = engine(current_seed, current_build)
                result_dict_check(result_row)

                if metric not in result_row:
                    raise ValueError(f"metric not found in result row: {metric}")

                sample_list.append(float(result_row[metric]))

            batch_mean = mean_value(sample_list)
            batch_mean_list.append(batch_mean)

        current_mean = mean_value(batch_mean_list)
        current_std = std_value(batch_mean_list)
        current_half_width = ci_half_width(batch_mean_list)

        # use max(..., 1.0) to avoid exploding relative width near zero
        denominator = max(abs(current_mean), 1.0)
        relative_half_width = current_half_width / denominator

        current_row = {
            "n": current_n,
            "mean": current_mean,
            "std": current_std,
            "ci_half_width": current_half_width,
            "relative_half_width": relative_half_width,
            "n_replicates": n_replicates,
        }
        result_rows.append(current_row)

    return result_rows


def recommend_n(sweep_result, target_relative=default_target_relative):
    """Smallest N whose relative_half_width <= target AND remains stable
    on the next grid point (i.e. two adjacent grid points both meet target).

    :return: int N or None if no grid point qualifies
    """
    if target_relative < 0:
        raise ValueError("target_relative must not be negative")

    if len(sweep_result) < 2:
        return None

    sorted_rows = sorted(sweep_result, key=lambda row: row["n"])

    # need two adjacent grid points to avoid one lucky small CI row
    # AI suggested the two-grid check, I kept it to avoid choosing one lucky N.
    for i in range(len(sorted_rows) - 1):
        current_row = sorted_rows[i]
        next_row = sorted_rows[i + 1]

        current_ok = current_row["relative_half_width"] <= target_relative
        next_ok = next_row["relative_half_width"] <= target_relative

        if current_ok and next_ok:
            return current_row["n"]

    return None
