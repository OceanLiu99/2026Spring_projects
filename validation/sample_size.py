"""Sample-size sweep and N_final recommendation for Phase 2 validation."""

import math
import statistics

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
