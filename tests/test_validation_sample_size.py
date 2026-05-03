import pytest

from validation.sample_size import ci_half_width

def test_ci_half_width_hand_calculated_five_samples():
    half_width = ci_half_width([1.0, 2.0, 3.0, 4.0, 5.0])

    assert round(half_width, 3) == 1.963


def test_ci_half_width_rejects_single_sample():
    with pytest.raises(ValueError):
        ci_half_width([1.0])
