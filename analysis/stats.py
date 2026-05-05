"""Small statistical helpers for H1/H2/H3 analysis tables.
I chose the test families around the experiment questions and kept each helper
small enough to check against the H1/H2/H3 tables.

Design notes:
- Welch t-statistic is computed by hand so the formula stays auditable.
  Only the p-value is delegated to scipy.stats.t.sf so the project does not
  re-derive the t-distribution survival function. When scipy is missing the
  t-stat is still returned and p_value is set to None (callers must check).
- Pearson r is computed via scipy.stats.pearsonr when available; a pure-python
  centered-sum fallback is provided so the analysis stage still runs in
  scipy-free environments (the fallback skips the p-value).
- All helpers reuse `mean_value`, `std_value`, `t_critical_value` from
  validation.sample_size so that validation and analysis share one numerical
  baseline (no risk of a second slightly-different t-table here).
"""

import math

from validation.sample_size import mean_value
from validation.sample_size import std_value
from validation.sample_size import t_critical_value

try:
    from scipy import stats
except ImportError:
    stats = None


# Fisher z-transform (atanh) diverges at exactly r = +/-1.
# Clamp r to (-1+eps, 1-eps) so the CI math stays finite when an analysis cell
# happens to be perfectly correlated (e.g. a degenerate single-luck-level cut).
fisher_z_clamp = 1.0 - 1e-6


def variance_value(samples):
    """Calculate sample variance.

    :param samples: list of numeric samples
    :return: float sample variance

    >>> variance_value([1, 2, 3])
    1.0
    """
    if len(samples) < 2:
        raise ValueError("at least two samples are required")

    current_std = std_value(samples)
    return current_std * current_std


def welch_degrees_freedom(a, b):
    """Calculate Welch-Satterthwaite degrees of freedom.

    :param a: first sample list
    :param b: second sample list
    :return: float degrees of freedom

    >>> round(welch_degrees_freedom([1, 2, 3], [2, 3, 4]), 3)
    4.0
    """
    if len(a) < 2 or len(b) < 2:
        raise ValueError("both groups need at least two samples")

    n_a = len(a)
    n_b = len(b)
    var_a = variance_value(a)
    var_b = variance_value(b)

    term_a = var_a / n_a
    term_b = var_b / n_b

    numerator = (term_a + term_b) * (term_a + term_b)
    denominator = (term_a * term_a) / (n_a - 1) + (term_b * term_b) / (n_b - 1)

    if denominator == 0:
        raise ValueError("welch denominator is zero")

    return numerator / denominator


def welch_t(a, b):
    """Calculate Welch t-test for two independent groups.

    The t-statistic is always computed locally (auditable formula). The
    p-value is computed via scipy.stats.t.sf when scipy is installed, and is
    returned as None otherwise -- callers should treat None as "not available"
    rather than as "not significant".

    :param a: first sample list
    :param b: second sample list
    :return: tuple (t_stat, p_value); p_value is None without scipy

    >>> result = welch_t([1, 2, 3], [2, 3, 4])
    >>> round(result[0], 3)
    -1.225
    """
    if len(a) < 2 or len(b) < 2:
        raise ValueError("both groups need at least two samples")

    n_a = len(a)
    n_b = len(b)
    mean_a = mean_value(a)
    mean_b = mean_value(b)
    var_a = variance_value(a)
    var_b = variance_value(b)

    denominator = math.sqrt(var_a / n_a + var_b / n_b)
    if denominator == 0:
        raise ValueError("welch denominator is zero")

    t_stat = (mean_a - mean_b) / denominator
    p_value = None

    if stats is not None:
        degrees_freedom = welch_degrees_freedom(a, b)
        p_value = float(stats.t.sf(abs(t_stat), degrees_freedom) * 2.0)

    return t_stat, p_value


def cohen_d(a, b):
    """Calculate pooled-standard-deviation Cohen's d.

    :param a: first sample list
    :param b: second sample list
    :return: float effect size

    >>> round(cohen_d([1, 2, 3], [2, 3, 4]), 3)
    -1.0
    """
    if len(a) < 2 or len(b) < 2:
        raise ValueError("both groups need at least two samples")

    n_a = len(a)
    n_b = len(b)
    mean_a = mean_value(a)
    mean_b = mean_value(b)
    var_a = variance_value(a)
    var_b = variance_value(b)

    pooled_variance = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
    pooled_std = math.sqrt(pooled_variance)

    if pooled_std == 0:
        if mean_a == mean_b:
            return 0.0
        raise ValueError("pooled standard deviation is zero")

    return (mean_a - mean_b) / pooled_std


def pearson_r_value(x, y):
    """Calculate Pearson correlation r.

    :param x: first numeric list
    :param y: second numeric list
    :return: float Pearson r

    >>> round(pearson_r_value([1, 2, 3], [2, 4, 6]), 3)
    1.0
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if len(x) < 2:
        raise ValueError("at least two points are required")

    x_mean = mean_value(x)
    y_mean = mean_value(y)
    numerator = 0.0
    x_square_sum = 0.0
    y_square_sum = 0.0

    # collect centered sums
    for i in range(len(x)):
        x_diff = float(x[i]) - x_mean
        y_diff = float(y[i]) - y_mean
        numerator += x_diff * y_diff
        x_square_sum += x_diff * x_diff
        y_square_sum += y_diff * y_diff

    denominator = math.sqrt(x_square_sum * y_square_sum)
    if denominator == 0:
        raise ValueError("correlation denominator is zero")

    return numerator / denominator


def pearson_with_ci(x, y, level=0.95):
    """Calculate Pearson r with Fisher-z confidence interval.

    Uses scipy.stats.pearsonr when available so r and p stay consistent with
    the wider scientific stack; falls back to the local centered-sum
    implementation (`pearson_r_value`) when scipy is missing, in which case
    p_value is None.

    :param x: first numeric list
    :param y: second numeric list
    :param level: confidence level
    :return: tuple (r, lo, hi, p_value); p_value is None without scipy

    >>> result = pearson_with_ci([1, 2, 3, 4], [2, 4, 6, 8])
    >>> round(result[0], 3)
    1.0
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if len(x) < 4:
        raise ValueError("at least four points are required")
    if level <= 0 or level >= 1:
        raise ValueError("level must be between 0 and 1")

    # one path or the other, never both -- avoids computing r twice
    if stats is not None:
        result = stats.pearsonr(x, y)
        r_value = float(result.statistic)
        p_value = float(result.pvalue)
    else:
        r_value = pearson_r_value(x, y)
        p_value = None

    # Fisher z transform cannot use exactly -1 or 1; see fisher_z_clamp note.
    bounded_r = max(min(r_value, fisher_z_clamp), -fisher_z_clamp)
    z_value = math.atanh(bounded_r)
    z_width = t_critical_value(len(x) - 3, level=level) / math.sqrt(len(x) - 3)

    low = math.tanh(z_value - z_width)
    high = math.tanh(z_value + z_width)
    return r_value, low, high, p_value


def mean_ci_95(samples):
    """Calculate mean and analytic 95% confidence interval.

    :param samples: list of numeric samples
    :return: tuple (mean, low, high)

    >>> result = mean_ci_95([1, 2, 3, 4, 5])
    >>> result[0]
    3.0
    """
    if len(samples) < 2:
        raise ValueError("at least two samples are required")

    current_mean = mean_value(samples)
    current_std = std_value(samples)
    half_width = t_critical_value(len(samples) - 1) * current_std / math.sqrt(len(samples))
    return current_mean, current_mean - half_width, current_mean + half_width
