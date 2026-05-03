"""Sensitivity checks for Phase 2 validation.
    Inspired by the logical validation part in the previous 2022 project."""

import math

from validation.contract import result_dict_check
from validation.sample_size import mean_value
from validation.sample_size import std_value

try:
    from scipy import stats
except ImportError:
    stats = None


default_n_per_value = 200


def value_as_number(value):
    """Convert an attribute value to a number for correlation.

    :param value: bool, int, or float attribute value
    :return: float value

    >>> value_as_number(True)
    1.0
    >>> value_as_number(False)
    0.0
    >>> value_as_number(4)
    4.0
    """
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return float(value)


def sweep_attribute(engine, base_build, attr_name, attr_values, metric,
                    n_per_value=default_n_per_value, seed_start=3000000000):
    """Run a one-attribute sensitivity sweep.

    :param engine: function like simple_mock_run(seed, build)
    :param base_build: base build dict copied for every run
    :param attr_name: build key to change, such as "luck_level"
    :param attr_values: values to sweep
    :param metric: output key to collect, such as "max_depth"
    :param n_per_value: number of runs for each attribute value
    :param seed_start: first validation seed
    :return: dict with row summaries and raw samples
    """
    if len(attr_values) == 0:
        raise ValueError("attr_values must not be empty")
    if n_per_value <= 0:
        raise ValueError("n_per_value must be positive")

    rows = []
    all_samples = []
    seed_offset = 0

    # sweep values
    for attr_value in attr_values:
        sample_list = []

        # collect samples for one value
        for i in range(n_per_value):
            current_seed = seed_start + seed_offset
            seed_offset += 1

            current_build = base_build.copy()
            current_build[attr_name] = attr_value
            result_row = engine(current_seed, current_build)
            result_dict_check(result_row)

            if metric not in result_row:
                raise ValueError(f"metric not found in result row: {metric}")

            sample_list.append(float(result_row[metric]))

        current_mean = mean_value(sample_list)
        current_std = 0.0
        if len(sample_list) >= 2:
            current_std = std_value(sample_list)

        current_row = {
            "attr_name": attr_name,
            "attr_value": attr_value,
            "metric": metric,
            "mean": current_mean,
            "std": current_std,
            "n": n_per_value,
        }
        rows.append(current_row)
        all_samples.append(sample_list)

    return {
        "attr_name": attr_name,
        "attr_values": list(attr_values),
        "metric": metric,
        "rows": rows,
        "samples": all_samples,
    }


def correlation_report(sweep_result):
    """Calculate Pearson correlation between attribute values and metric means.

    :param sweep_result: dict returned by sweep_attribute
    :return: dict with r and p_value
    """
    rows = sweep_result["rows"]
    if len(rows) < 2:
        raise ValueError("at least two rows are required")

    attr_values = []
    metric_values = []

    # collect points
    for row in rows:
        attr_values.append(value_as_number(row["attr_value"]))
        metric_values.append(float(row["mean"]))

    if stats is not None:
        result = stats.pearsonr(attr_values, metric_values)
        return {
            "attr_name": sweep_result["attr_name"],
            "metric": sweep_result["metric"],
            "r": float(result.statistic),
            "p_value": float(result.pvalue),
            "n_points": len(rows),
        }

    # fallback Pearson r for local venvs without scipy
    attr_mean = mean_value(attr_values)
    metric_mean = mean_value(metric_values)
    numerator = 0.0
    attr_square_sum = 0.0
    metric_square_sum = 0.0

    for i in range(len(attr_values)):
        attr_diff = attr_values[i] - attr_mean
        metric_diff = metric_values[i] - metric_mean
        numerator += attr_diff * metric_diff
        attr_square_sum += attr_diff * attr_diff
        metric_square_sum += metric_diff * metric_diff

    denominator = math.sqrt(attr_square_sum * metric_square_sum)
    if denominator == 0:
        raise ValueError("correlation denominator is zero")

    return {
        "attr_name": sweep_result["attr_name"],
        "metric": sweep_result["metric"],
        "r": numerator / denominator,
        "p_value": None,
        "n_points": len(rows),
    }


def validate_monotonic(sweep_result, expected_sign="+"):
    """Check whether metric means move in the expected direction.

    :param sweep_result: dict returned by sweep_attribute
    :param expected_sign: "+" for increasing, "-" for decreasing
    :return: summary dict

    >>> validate_monotonic({"rows": [{"mean": 1}, {"mean": 2}]})["passed"]
    True
    """
    if expected_sign not in ("+", "-"):
        raise ValueError("expected_sign must be '+' or '-'")

    rows = sweep_result["rows"]
    if len(rows) < 2:
        raise ValueError("at least two rows are required")

    passed = True

    # check adjacent means
    for i in range(len(rows) - 1):
        current_mean = rows[i]["mean"]
        next_mean = rows[i + 1]["mean"]

        if expected_sign == "+" and next_mean < current_mean:
            passed = False
        if expected_sign == "-" and next_mean > current_mean:
            passed = False

    return {
        "attr_name": sweep_result.get("attr_name"),
        "metric": sweep_result.get("metric"),
        "expected_sign": expected_sign,
        "passed": passed,
    }
