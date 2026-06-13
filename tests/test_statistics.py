from __future__ import annotations

import math

import pytest

from cons_trukt.statistics import bootstrap_interval, wilson_interval


def test_wilson_zero_total_is_empty():
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_wilson_perfect_score_has_upper_bound_one_lower_below_one():
    lo, hi = wilson_interval(10, 10)
    assert hi == 1.0
    assert lo < 1.0  # 10/10 is not certainty -> CI must admit uncertainty


def test_wilson_small_sample_is_wider_than_large_sample():
    small = wilson_interval(8, 10)
    large = wilson_interval(80, 100)
    assert (small[1] - small[0]) > (large[1] - large[0])


def test_wilson_brackets_point_estimate():
    lo, hi = wilson_interval(7, 10)
    assert lo <= 0.7 <= hi


def test_wilson_rejects_out_of_range():
    with pytest.raises(ValueError):
        wilson_interval(11, 10)


def test_bootstrap_constant_values_has_zero_width():
    lo, hi = bootstrap_interval([1.0] * 50)
    assert math.isclose(lo, 1.0) and math.isclose(hi, 1.0)


def test_bootstrap_is_deterministic():
    vals = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    assert bootstrap_interval(vals) == bootstrap_interval(vals)


def test_bootstrap_brackets_mean():
    vals = [1.0, 0.0] * 25
    lo, hi = bootstrap_interval(vals)
    assert lo <= 0.5 <= hi
