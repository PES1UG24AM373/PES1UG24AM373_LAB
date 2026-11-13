from hypothesis import given, strategies as st
from processor import parse_season_pass_validity, compute_trail_gradient, calculate_lift_access_tier

# Fuzz inputs: arbitrary Unicode text, or None (to simulate missing input)
fuzz_input = st.text() | st.none()


@given(fuzz_input)
def test_parse_season_pass_validity_no_crash(s):
    try:
        parse_season_pass_validity(s)
    except Exception as e:
        assert False, f"parse_season_pass_validity crashed with: {e!r} for input {s!r}"


@given(fuzz_input)
def test_compute_trail_gradient_safe(s):
    try:
        compute_trail_gradient(s)
    except Exception as e:
        assert False, f"compute_trail_gradient crashed with: {e!r} for input {s!r}"


@given(fuzz_input)
def test_calculate_lift_access_tier_safe(s):
    try:
        calculate_lift_access_tier(s)
    except Exception as e:
        assert False, f"calculate_lift_access_tier crashed with: {e!r} for input {s!r}"


# ---------------------------------------------------------------------------
# Additional property checks (beyond "does not crash"): the outputs must be
# well-formed, and valid inputs must still produce correct results.
# ---------------------------------------------------------------------------

@given(st.integers(2026, 9999), st.integers(1, 12), st.integers(1, 28))
def test_valid_dates_report_valid(y, m, d):
    result = parse_season_pass_validity(f"{y}/{m}/{d}")
    assert result == f"Pass Expiry: {y:04d}-{m:02d}-{d:02d} (VALID)"


@given(st.integers(1, 2025), st.integers(1, 12), st.integers(1, 28))
def test_past_dates_report_expired(y, m, d):
    result = parse_season_pass_validity(f"{y}/{m}/{d}")
    assert result.endswith("(EXPIRED)")


@given(fuzz_input)
def test_parse_returns_string(s):
    assert isinstance(parse_season_pass_validity(s), str)


@given(st.floats(-1e6, 1e6), st.floats(0.001, 1e6))
def test_gradient_matches_formula(drop, dist):
    result = compute_trail_gradient(f"{drop}:{dist}")
    assert result == round((drop / dist) * 100.0, 2)


@given(fuzz_input)
def test_gradient_returns_none_or_finite_float(s):
    result = compute_trail_gradient(s)
    assert result is None or (isinstance(result, float) and result == result
                              and abs(result) != float("inf"))


@given(st.sampled_from(["0", "0.0", "-0", "0e5", "+0", " 0 "]), st.floats(-1e6, 1e6))
def test_gradient_zero_distance_is_handled(dist, drop):
    # Division by zero must never escape as an exception
    assert compute_trail_gradient(f"{drop}:{dist}") is None


@given(st.sampled_from(["BEG", "INT", "ADV", "ALL"]), st.sampled_from(["", " ", "\t"]))
def test_known_zones_return_price(zone, pad):
    price = calculate_lift_access_tier(pad + zone.lower() + pad)
    assert price in (35.0, 60.0, 85.0, 110.0)


@given(fuzz_input)
def test_tier_returns_none_or_known_price(s):
    assert calculate_lift_access_tier(s) in (None, 35.0, 60.0, 85.0, 110.0)
