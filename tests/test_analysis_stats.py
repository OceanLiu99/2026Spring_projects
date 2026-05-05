from analysis.stats import cohen_d
from analysis.stats import mean_ci_95
from analysis.stats import pearson_with_ci
from analysis.stats import welch_t


def test_cohen_d_matches_hand_calculation():
    assert round(cohen_d([1, 2, 3], [2, 3, 4]), 3) == -1.0


def test_welch_t_returns_expected_direction():
    t_stat, p_value = welch_t([1, 2, 3], [3, 4, 5])

    assert t_stat < 0
    assert p_value is None or p_value > 0.0


def test_mean_ci_95_shrinks_with_more_samples():
    short_mean, short_low, short_high = mean_ci_95([1, 2, 3, 4, 5])
    long_mean, long_low, long_high = mean_ci_95([1, 2, 3, 4, 5] * 2)

    short_width = short_high - short_low
    long_width = long_high - long_low

    assert short_mean == long_mean
    assert long_width < short_width


def test_pearson_positive_relation_has_positive_r():
    r_value, low, high, p_value = pearson_with_ci(
        [1, 2, 3, 4, 5],
        [2, 3, 5, 4, 6],
    )

    assert r_value > 0
    assert low <= r_value <= high
    assert p_value is None or p_value >= 0.0
