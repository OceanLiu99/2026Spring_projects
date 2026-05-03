"""
By using a rolling-window criterion, test convergence of MC simulation output.
"""

from validation.contract import result_dict_check

default_window = 50
default_rel_tol = 0.01
default_min_n = 100

def convergence_test(values: list, window=default_window,
                     rel_tol=default_rel_tol, min_n=default_min_n):
    """Check whether running means are stable in a recent window.

    :param values: list of numeric samples
    :param window: number of recent running means to inspect
    :param rel_tol: allowed relative drift inside the window
    :param min_n: minimum sample size before convergence is allowed
    :return: convergence summary dict

    # Example below: If there are 120 samples, each of which is 10.
    Start checking from the 50th sample onward.
    Examine the running mean of the most recent 20 samples each time.
    If the fluctuation in the running mean of the most recent 20 samples is ≤ 1%,
    it is considered to have converged.

    >>> result = convergence_test([10.0] * 120, window=20, rel_tol=0.01, min_n=50)
    >>> result["converged"]
    True
    >>> result["n_required"] >= 50
    True
    >>> result["final_mean"] == 10.0
    True
    """
    # condition check
    if window <= 0:
        raise ValueError("window must be positive")
    if min_n <= 0:
        raise ValueError("min_n must be positive")
    if rel_tol < 0:
        raise ValueError("rel_tol must not be negative")

    mean_list = processing_mean(values)
    sample_count = len(mean_list)

    summary = {
        "converged": False,
        "n_required": None,
        "final_mean": None,
        "final_drift": None,
        "window": window,
        "rel_tol": rel_tol,
        "min_n": min_n,
        "n": sample_count,
    }

    # corner case
    if sample_count == 0:
        return summary

    summary["final_mean"] = mean_list[-1]

    # not enough data to inspect one whole window
    start_n = max(window, min_n)
    if sample_count < start_n:
        return summary

    # scan possible convergence point
    for end_n in range(start_n, sample_count + 1):
        current_window = mean_list[end_n - window:end_n]
        current_high = max(current_window)
        current_low = min(current_window)
        current_mean = abs(mean_list[end_n - 1])

        # avoid division by a tiny mean
        denominator = max(current_mean, 1.0)
        current_drift = (current_high - current_low) / denominator

        # check convergence criterion
        if current_drift <= rel_tol:
            summary["converged"] = True
            summary["n_required"] = end_n
            summary["final_drift"] = current_drift
            return summary

    # report final window drift even if it did not converge
    final_window = mean_list[sample_count - window:sample_count]
    final_high = max(final_window)
    final_low = min(final_window)
    denominator = max(abs(mean_list[-1]), 1.0)
    summary["final_drift"] = (final_high - final_low) / denominator
    return summary

def processing_mean(values: list):
    """Return cumulative mean after each new sample.

    :param values: list of numeric samples
    :return: list of running means

    >>> processing_mean([10, 20, 30])
    [10.0, 15.0, 20.0]
    >>> processing_mean([])
    []
    """
    mean_list = []
    current_total = 0.0

    # corner case
    if len(values) == 0:
        return mean_list

    # calculate running mean
    for i in range(len(values)):
        current_total += float(values[i])
        current_count = i + 1
        current_mean = current_total / current_count
        mean_list.append(current_mean)

    return mean_list

def assess_engine(engine, build: dict, metric: str, n_runs=200,
                  seed_start=0, window=default_window,
                  rel_tol=default_rel_tol, min_n=default_min_n):
    """Run an engine repeatedly and check convergence for one metric.

    :param engine: function like simple_mock_run(seed, build)
    :param build: config dict for the engine
    :param metric: output key to collect, such as "max_depth"
    :param n_runs: number of runs to collect
    :param seed_start: first seed value
    :return: convergence summary dict with samples included
    """
    # condition check
    if n_runs <= 0:
        raise ValueError("n_runs must be positive")

    sample_list = []

    # collect samples
    for i in range(n_runs):
        current_seed = seed_start + i
        current_build = build.copy()
        result_row = engine(current_seed, current_build)
        result_dict_check(result_row)

        if metric not in result_row:
            raise ValueError(f"metric not found in result row: {metric}")

        sample_list.append(float(result_row[metric]))

    summary = convergence_test(
        sample_list,
        window=window,
        rel_tol=rel_tol,
        min_n=min_n,
    )
    summary["metric"] = metric
    summary["samples"] = sample_list
    return summary
