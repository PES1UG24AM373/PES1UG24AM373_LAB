"""
Lab 6 - CODE (LINE) COVERAGE test suite for ski_resort_pass.py
==============================================================

Target : >= 90 % line coverage of ski_resort_pass.py

Run it : coverage run -m pytest CodeCoverageTest_ski_resort_pass_application.py
         coverage report -m

Strategy
--------
Line coverage only asks "was this line executed at least once?", so this suite
has one focused test for every outcome / statement group in the module:
the guard clause, every pass duration, every skier category, gear rental,
lodge locker, blackout handling, every status code, and every anemometer result.

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
# Helpers (keep the test bodies short and readable)
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


# --------------------------------------------------------------------------- #
# process_resort_bookings - input validation and empty / skipped input
# --------------------------------------------------------------------------- #
def test_invalid_groups_type_raises_value_error():
    # guard clause: groups must be a list
    with pytest.raises(ValueError, match="Invalid groups list or facility fee"):
        process_resort_bookings("not a list", 10.0)


def test_empty_group_list_is_zero_sales():
    # outer loop never runs -> revenue stays 0.0 -> ZERO_SALES
    assert_result(process_resort_bookings([], 15.0), 0.0, "ZERO_SALES")


def test_inactive_group_is_skipped():
    # `continue` for inactive groups; nothing else is billed
    groups = [make_group([make_skier(30)], active=False)]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


# --------------------------------------------------------------------------- #
# process_resort_bookings - pass durations (every if / elif / else arm)
# --------------------------------------------------------------------------- #
def test_season_pass_single_adult():
    groups = [make_group([make_skier(30)], duration="season")]
    assert_result(process_resort_bookings(groups, 15.0), 300.0, "COMPLETED")


def test_full_day_adult_with_gear_and_lodge_locker():
    # 80 (adult) + 35 (gear) + 15 (locker fee) = 130
    groups = [make_group([make_skier(30, gear=True)], duration="full_day", locker=True)]
    assert_result(process_resort_bookings(groups, 15.0), 130.0, "COMPLETED")


def test_half_day_pass_single_adult():
    groups = [make_group([make_skier(30)], duration="half_day")]
    assert_result(process_resort_bookings(groups, 15.0), 50.0, "COMPLETED")


def test_unknown_duration_is_rejected():
    # `else` arm: rejected pass, group skipped; 1 rejection is not > 4
    groups = [make_group([make_skier(30)], duration="weekend")]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


# --------------------------------------------------------------------------- #
# process_resort_bookings - skier categories
# --------------------------------------------------------------------------- #
def test_child_pays_sixty_percent():
    # age 8 -> 80 * 0.60 = 48
    groups = [make_group([make_skier(8)])]
    assert_result(process_resort_bookings(groups, 15.0), 48.0, "COMPLETED")


def test_senior_pays_seventy_percent():
    # age 70 -> 80 * 0.70 = 56
    groups = [make_group([make_skier(70)])]
    assert_result(process_resort_bookings(groups, 15.0), 56.0, "COMPLETED")


def test_non_positive_age_is_rejected():
    # age <= 0 -> rejected pass, skier skipped
    groups = [make_group([make_skier(0)])]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


# --------------------------------------------------------------------------- #
# process_resort_bookings - blackout override
# --------------------------------------------------------------------------- #
def test_blackout_override_full_day_pays_half_rate():
    # blackout skier on a full_day pass: rejected, but still billed 80 * 0.50 = 40
    groups = [make_group([make_skier(30, blackout=True)], duration="full_day")]
    assert_result(process_resort_bookings(groups, 15.0), 40.0, "COMPLETED")


def test_blackout_override_half_day_voids_whole_group():
    # adult adds 50, blackout resets the group total to 0 and `break`s,
    # so the third skier is never processed -> 0 revenue
    skiers = [make_skier(30), make_skier(30, blackout=True), make_skier(30)]
    groups = [make_group(skiers, duration="half_day")]
    assert_result(process_resort_bookings(groups, 15.0), 0.0, "ZERO_SALES")


# --------------------------------------------------------------------------- #
# process_resort_bookings - audit status
# --------------------------------------------------------------------------- #
def test_more_than_four_rejections_triggers_audit_review():
    # 1 adult (80) + 5 invalid ages -> 5 rejections (> 4) -> AUDIT_REVIEW
    skiers = [make_skier(30)] + [make_skier(0) for _ in range(5)]
    groups = [make_group(skiers)]
    assert_result(process_resort_bookings(groups, 15.0), 80.0, "AUDIT_REVIEW")


# --------------------------------------------------------------------------- #
# check_chairlift_anemometer
# --------------------------------------------------------------------------- #
def test_anemometer_no_data():
    assert check_chairlift_anemometer([]) == "NO_DATA"


def test_anemometer_two_consecutive_gusts_suspends_lift():
    assert check_chairlift_anemometer([[10, 50, 60]]) == "SUSPEND_LIFT"


def test_anemometer_calm_winds_are_safe():
    assert check_chairlift_anemometer([[10, 20, 30]]) == "SAFE_OPERATION"


def test_anemometer_single_gust_then_calm_resets_streak():
    # 50 (streak 1) -> 10 (reset) -> 50 (streak 1 again): never reaches 2
    assert check_chairlift_anemometer([[50, 10, 50]]) == "SAFE_OPERATION"
