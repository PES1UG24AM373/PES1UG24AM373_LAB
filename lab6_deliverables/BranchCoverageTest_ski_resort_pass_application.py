"""
Lab 6 - BRANCH COVERAGE test suite for ski_resort_pass.py
=========================================================

Target : >= 90 % BRANCH coverage of ski_resort_pass.py

Run it : coverage run --branch -m pytest BranchCoverageTest_ski_resort_pass_application.py
         coverage report -m

Strategy
--------
This file is self-contained: it keeps every test from the code-coverage suite
(PART 1) and adds decision-focused tests (PART 2) so that EVERY decision is
exercised on BOTH its True and False side:

  * guard clause          - each operand of `not isinstance(...) or fee < 0`
                            on its own, plus the fee == 0 boundary
  * `.get()` defaults     - missing is_active / duration / skiers / age / flags
  * duration if/elif/else - all four arms, plus near-miss strings
  * skier categories      - the boundaries 0/1, 11/12, 64/65
  * blackout override     - half_day (break) vs other durations, priority over
                            the age category, interaction with gear/locker
  * loops                 - zero, one and many iterations; `break` vs normal exit
  * status decisions      - the `> 4` threshold (4 vs 5) and AUDIT_REVIEW taking
                            priority over ZERO_SALES
  * anemometer            - the `> 45` and `>= 2` boundaries, streak reset,
                            streak NOT carrying over between lifts

Pricing rules used to derive the expected values by hand
--------------------------------------------------------
    base rate          season 300 | full_day 80 | half_day 50
    child  (age < 12)  60 % of base          senior (age >= 65)  70 % of base
    adult              100 % of base         gear rental         +35 per skier
    lodge locker       + facility_fee per group
    blackout override  skier counts as rejected and pays 50 % of base,
                       BUT on a half_day pass the whole group total is voided
    status             AUDIT_REVIEW if rejected passes > 4,
                       else ZERO_SALES if revenue == 0, else COMPLETED
"""
import pytest

from ski_resort_pass import process_resort_bookings, check_chairlift_anemometer


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def make_skier(age=30, gear=False, blackout=False):
    return {"age": age, "gear_rental": gear, "blackout_override": blackout}


def make_group(skiers, duration="full_day", locker=False, active=True):
    return {
        "is_active": active,
        "duration": duration,
        "includes_lodge_locker": locker,
        "skiers": skiers,
    }


def assert_result(result, revenue, status):
    assert result["total_revenue"] == pytest.approx(revenue)
    assert result["status"] == status


# =========================================================================== #
# PART 1 - tests carried over from the code-coverage suite
# =========================================================================== #
def test_invalid_groups_type_raises_value_error():
    with pytest.raises(ValueError, match="Invalid groups list or facility fee"):
        process_resort_bookings("not a list", 10.0)


def test_empty_group_list_is_zero_sales():
    assert_result(process_resort_bookings([], 15.0), 0.0, "ZERO_SALES")


def test_inactive_group_is_skipped():
    groups = [make_group([make_skier(30)], active=False)]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_season_pass_single_adult():
    groups = [make_group([make_skier(30)], duration="season")]
    assert_result(process_resort_bookings(groups, 15.0), 300.0, "COMPLETED")


def test_full_day_adult_with_gear_and_lodge_locker():
    # 80 + 35 (gear) + 15 (locker) = 130
    groups = [make_group([make_skier(30, gear=True)], duration="full_day", locker=True)]
    assert_result(process_resort_bookings(groups, 15.0), 130.0, "COMPLETED")


def test_half_day_pass_single_adult():
    groups = [make_group([make_skier(30)], duration="half_day")]
    assert_result(process_resort_bookings(groups, 15.0), 50.0, "COMPLETED")


def test_unknown_duration_is_rejected():
    groups = [make_group([make_skier(30)], duration="weekend")]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_child_pays_sixty_percent():
    groups = [make_group([make_skier(8)])]
    assert_result(process_resort_bookings(groups, 15.0), 48.0, "COMPLETED")


def test_senior_pays_seventy_percent():
    groups = [make_group([make_skier(70)])]
    assert_result(process_resort_bookings(groups, 15.0), 56.0, "COMPLETED")


def test_non_positive_age_is_rejected():
    groups = [make_group([make_skier(0)])]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_blackout_override_full_day_pays_half_rate():
    groups = [make_group([make_skier(30, blackout=True)], duration="full_day")]
    assert_result(process_resort_bookings(groups, 15.0), 40.0, "COMPLETED")


def test_blackout_override_half_day_voids_whole_group():
    skiers = [make_skier(30), make_skier(30, blackout=True), make_skier(30)]
    groups = [make_group(skiers, duration="half_day")]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_more_than_four_rejections_triggers_audit_review():
    skiers = [make_skier(30)] + [make_skier(0) for _ in range(5)]
    groups = [make_group(skiers)]
    assert_result(process_resort_bookings(groups, 15.0), 80.0, "AUDIT_REVIEW")


def test_anemometer_no_data():
    assert check_chairlift_anemometer([]) == "NO_DATA"


def test_anemometer_two_consecutive_gusts_suspends_lift():
    assert check_chairlift_anemometer([[10, 50, 60]]) == "SUSPEND_LIFT"


def test_anemometer_calm_winds_are_safe():
    assert check_chairlift_anemometer([[10, 20, 30]]) == "SAFE_OPERATION"


def test_anemometer_single_gust_then_calm_resets_streak():
    assert check_chairlift_anemometer([[50, 10, 50]]) == "SAFE_OPERATION"


# =========================================================================== #
# PART 2 - additional BRANCH / decision / boundary tests
# =========================================================================== #

# --- 1. Guard clause: `not isinstance(groups, list) or facility_fee < 0` ----- #
@pytest.mark.parametrize(
    "bad_groups",
    [None, "groups", (), {}, 42],
    ids=["None", "str", "tuple", "dict", "int"],
)
def test_guard_first_operand_every_non_list_type_raises(bad_groups):
    # left operand of `or` is True -> raises even though the fee is valid
    with pytest.raises(ValueError, match="Invalid groups list or facility fee"):
        process_resort_bookings(bad_groups, 10.0)


@pytest.mark.parametrize("fee", [-0.01, -1, -100.0])
def test_guard_second_operand_negative_fee_raises(fee):
    # left operand False (valid list), right operand True
    with pytest.raises(ValueError, match="Invalid groups list or facility fee"):
        process_resort_bookings([], fee)


def test_guard_zero_fee_is_the_valid_boundary():
    # fee == 0 is NOT < 0: both operands False -> no exception
    assert_result(process_resort_bookings([], 0), 0.0, "ZERO_SALES")


def test_zero_fee_locker_adds_nothing():
    groups = [make_group([make_skier(30)], locker=True)]
    assert_result(process_resort_bookings(groups, 0), 80.0, "COMPLETED")


# --- 2. Group-level decisions and .get() defaults --------------------------- #
def test_group_without_is_active_defaults_to_inactive():
    groups = [{"duration": "full_day", "skiers": [make_skier(30)]}]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_group_without_duration_defaults_to_full_day():
    groups = [{"is_active": True, "skiers": [make_skier(30)]}]
    assert_result(process_resort_bookings(groups, 15.0), 80.0, "COMPLETED")


def test_group_without_skiers_defaults_to_empty_list():
    # inner loop runs zero times
    groups = [{"is_active": True, "duration": "season"}]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_active_group_with_no_skiers_still_pays_locker_fee():
    # zero-iteration inner loop, locker decision True
    groups = [make_group([], locker=True)]
    assert_result(process_resort_bookings(groups, 15.0), 15.0, "COMPLETED")


def test_inactive_group_never_pays_locker_fee():
    groups = [make_group([make_skier(30)], locker=True, active=False)]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_unknown_duration_group_skips_skiers_and_locker_fee():
    # `continue` in the else-arm jumps over the locker decision entirely
    groups = [make_group([make_skier(30)], duration="weekend", locker=True)]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


@pytest.mark.parametrize(
    "duration",
    ["FULL_DAY", "Season", "half-day", "", None],
    ids=["upper-case", "capitalised", "hyphen", "empty-string", "None"],
)
def test_duration_match_is_exact_so_near_misses_are_rejected(duration):
    groups = [make_group([make_skier(30)], duration=duration)]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


# --- 3. Skier category boundaries ------------------------------------------- #
@pytest.mark.parametrize(
    "age, revenue, status",
    [
        (-1, 0.0, "ZERO_SALES"),    # invalid
        (0, 0.0, "ZERO_SALES"),     # last invalid age  (age <= 0)
        (1, 48.0, "COMPLETED"),     # first valid age   -> child 60 %
        (11, 48.0, "COMPLETED"),    # last child age    (age < 12)
        (12, 80.0, "COMPLETED"),    # first adult age
        (64, 80.0, "COMPLETED"),    # last adult age
        (65, 56.0, "COMPLETED"),    # first senior age  (age >= 65)
        (100, 56.0, "COMPLETED"),   # very old senior
    ],
)
def test_age_boundaries_on_full_day_pass(age, revenue, status):
    groups = [make_group([make_skier(age)])]
    assert_result(process_resort_bookings(groups, 0.0), revenue, status)


def test_skier_with_no_keys_defaults_to_age_zero_and_is_rejected():
    groups = [make_group([{}])]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_skier_with_only_age_has_no_gear_and_no_blackout():
    groups = [make_group([{"age": 30}])]
    assert_result(process_resort_bookings(groups, 15.0), 80.0, "COMPLETED")


# --- 4. Gear rental decision ------------------------------------------------ #
@pytest.mark.parametrize(
    "age, revenue",
    [(8, 83.0), (30, 115.0), (70, 91.0)],   # 48+35, 80+35, 56+35
    ids=["child", "adult", "senior"],
)
def test_gear_rental_adds_35_for_every_skier_category(age, revenue):
    groups = [make_group([make_skier(age, gear=True)])]
    assert_result(process_resort_bookings(groups, 15.0), revenue, "COMPLETED")


def test_gear_rental_is_charged_per_skier():
    groups = [make_group([make_skier(30, gear=True), make_skier(30, gear=True)])]
    assert_result(process_resort_bookings(groups, 15.0), 230.0, "COMPLETED")


def test_gear_rental_not_charged_for_rejected_age():
    # `continue` on invalid age happens before the gear decision
    groups = [make_group([make_skier(0, gear=True)])]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


# --- 5. Blackout override decisions ----------------------------------------- #
def test_blackout_with_gear_on_full_day_pays_half_rate_plus_gear():
    # 80 * 0.50 + 35 = 75 (blackout branch falls through to the gear decision)
    groups = [make_group([make_skier(30, gear=True, blackout=True)])]
    assert_result(process_resort_bookings(groups, 15.0), 75.0, "COMPLETED")


def test_blackout_on_season_pass_pays_half_rate():
    groups = [make_group([make_skier(30, blackout=True)], duration="season")]
    assert_result(process_resort_bookings(groups, 15.0), 150.0, "COMPLETED")


def test_half_day_blackout_as_first_skier_skips_the_rest_of_the_group():
    skiers = [make_skier(30, blackout=True), make_skier(30)]
    groups = [make_group(skiers, duration="half_day")]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_half_day_blackout_breaks_before_gear_is_charged():
    skiers = [make_skier(30, gear=True), make_skier(30, gear=True, blackout=True)]
    groups = [make_group(skiers, duration="half_day")]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


def test_half_day_blackout_still_pays_locker_fee():
    # `break` only leaves the skier loop; the locker decision after it still runs.
    # (Characterisation test: pins the module's current behaviour.)
    skiers = [make_skier(30), make_skier(30, blackout=True)]
    groups = [make_group(skiers, duration="half_day", locker=True)]
    assert_result(process_resort_bookings(groups, 15.0), 15.0, "COMPLETED")


def test_half_day_blackout_only_voids_its_own_group():
    # `break` leaves the inner loop only; the next group is still processed
    groups = [
        make_group([make_skier(30, blackout=True)], duration="half_day"),
        make_group([make_skier(30)], duration="full_day"),
    ]
    assert_result(process_resort_bookings(groups, 15.0), 80.0, "COMPLETED")


def test_invalid_age_is_checked_before_blackout_so_group_is_not_voided():
    # age <= 0 -> rejected + `continue`; the half_day void logic is never reached
    skiers = [make_skier(0, blackout=True), make_skier(30)]
    groups = [make_group(skiers, duration="half_day")]
    assert_result(process_resort_bookings(groups, 15.0), 50.0, "COMPLETED")


@pytest.mark.parametrize("age", [8, 70], ids=["child", "senior"])
def test_blackout_takes_priority_over_age_discount(age):
    # blackout arm is tested before the child / senior arms: 80 * 0.50, not 48 / 56
    groups = [make_group([make_skier(age, blackout=True)])]
    assert_result(process_resort_bookings(groups, 15.0), 40.0, "COMPLETED")


# --- 6. Combined / multi-group scenarios ------------------------------------ #
def test_mixed_family_on_season_pass_with_gear_and_locker():
    # child 180 + adult 300 + senior 210 + senior gear 35 + locker 20 = 745
    skiers = [make_skier(8), make_skier(30), make_skier(70, gear=True)]
    groups = [make_group(skiers, duration="season", locker=True)]
    assert_result(process_resort_bookings(groups, 20.0), 745.0, "COMPLETED")


def test_revenue_accumulates_across_groups_and_skips_inactive_ones():
    groups = [
        make_group([make_skier(30)]),                                   # 80
        make_group([make_skier(30)], active=False),                     # skipped
        make_group([make_skier(8)], duration="half_day"),               # 30
        make_group([make_skier(70)], duration="season", locker=True),   # 210 + 10
    ]
    assert_result(process_resort_bookings(groups, 10.0), 330.0, "COMPLETED")


# --- 7. Status decisions: `> 4` threshold and priority order ---------------- #
@pytest.mark.parametrize(
    "invalid_skiers, status",
    [
        (0, "COMPLETED"),
        (4, "COMPLETED"),        # exactly 4 rejections: NOT > 4
        (5, "AUDIT_REVIEW"),     # first count that is > 4
        (6, "AUDIT_REVIEW"),
    ],
)
def test_audit_review_threshold_is_strictly_greater_than_four(invalid_skiers, status):
    skiers = [make_skier(30)] + [make_skier(0) for _ in range(invalid_skiers)]
    groups = [make_group(skiers)]
    assert_result(process_resort_bookings(groups, 15.0), 80.0, status)


def test_audit_review_takes_priority_over_zero_sales():
    # revenue is 0.0 but 5 rejections -> AUDIT_REVIEW wins (checked first)
    groups = [make_group([make_skier(0) for _ in range(5)])]
    result = process_resort_bookings(groups, 15.0)
    assert result == {"total_revenue": 0.0, "status": "AUDIT_REVIEW"}


def test_rejections_accumulate_across_all_rejection_sources():
    # 2 unknown durations + 1 blackout + 2 invalid ages = 5 rejections; revenue = 40
    groups = [
        make_group([make_skier(30)], duration="weekend"),
        make_group([make_skier(30)], duration="monthly"),
        make_group([make_skier(30, blackout=True), make_skier(0), make_skier(-5)]),
    ]
    assert_result(process_resort_bookings(groups, 15.0), 40.0, "AUDIT_REVIEW")


@pytest.mark.parametrize(
    "fee, expected",
    [(10.126, 90.13), (10.124, 90.12)],   # 80 + fee, rounded to 2 decimals
)
def test_total_revenue_is_rounded_to_two_decimals(fee, expected):
    groups = [make_group([make_skier(30)], locker=True)]
    result = process_resort_bookings(groups, fee)
    assert result["total_revenue"] == expected
    assert result["status"] == "COMPLETED"


# --- 8. check_chairlift_anemometer ------------------------------------------ #
def test_anemometer_none_is_no_data():
    assert check_chairlift_anemometer(None) == "NO_DATA"


@pytest.mark.parametrize("streams", [[[]], [[], []]], ids=["one-empty-lift", "two-empty-lifts"])
def test_anemometer_lifts_with_no_readings_are_safe(streams):
    # non-empty outer list, but the inner loop runs zero times
    assert check_chairlift_anemometer(streams) == "SAFE_OPERATION"


@pytest.mark.parametrize(
    "streams, expected",
    [
        pytest.param([[45, 45, 45]], "SAFE_OPERATION", id="45mph-is-not-a-gust"),
        pytest.param([[45.0, 45.0]], "SAFE_OPERATION", id="45.0-float-is-not-a-gust"),
        pytest.param([[46, 46]], "SUSPEND_LIFT", id="46mph-twice-is-a-streak"),
        pytest.param([[45.1, 45.1]], "SUSPEND_LIFT", id="45.1-float-twice-is-a-streak"),
        pytest.param([[46]], "SAFE_OPERATION", id="single-gust-single-reading"),
        pytest.param([[10, 46]], "SAFE_OPERATION", id="single-gust-at-the-end"),
        pytest.param([[45, 46]], "SAFE_OPERATION", id="calm-then-one-gust"),
        pytest.param([[46, 45, 46]], "SAFE_OPERATION", id="boundary-45-resets-streak"),
        pytest.param([[50, 50, 50]], "SUSPEND_LIFT", id="three-gusts"),
        pytest.param([[50, 10, 50, 50]], "SUSPEND_LIFT", id="streak-restarts-after-reset"),
        pytest.param([[0, -5, -50]], "SAFE_OPERATION", id="zero-and-negative-speeds"),
    ],
)
def test_anemometer_gust_threshold_and_streak_boundaries(streams, expected):
    assert check_chairlift_anemometer(streams) == expected


def test_anemometer_streak_does_not_carry_over_between_lifts():
    # lift 1 ends on a gust, lift 2 starts with one: streak is reset per lift
    assert check_chairlift_anemometer([[10, 50], [50, 10]]) == "SAFE_OPERATION"
    assert check_chairlift_anemometer([[50], [50]]) == "SAFE_OPERATION"


def test_anemometer_second_lift_can_trigger_suspension():
    assert check_chairlift_anemometer([[10, 20], [60, 60]]) == "SUSPEND_LIFT"


def test_anemometer_returns_as_soon_as_a_lift_is_unsafe():
    assert check_chairlift_anemometer([[50, 50], [10]]) == "SUSPEND_LIFT"
