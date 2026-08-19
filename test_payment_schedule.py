from datetime import date

import pytest

from payment_schedule import (
    days_in_month,
    add_months,
    is_business_day,
    next_business_day,
    prev_business_day,
    adjust,
    parse_frequency,
)


def test_days_in_month_regular():
    assert days_in_month(2026, 1) == 31
    assert days_in_month(2026, 4) == 30


def test_days_in_month_december():
    assert days_in_month(2026, 12) == 31


def test_days_in_month_february_leap_year():
    assert days_in_month(2024, 2) == 29


def test_days_in_month_february_non_leap_year():
    assert days_in_month(2026, 2) == 28


def test_add_months_within_year():
    assert add_months(date(2023, 10, 5), 2) == date(2023, 12, 5)


def test_add_months_crosses_year_boundary():
    assert add_months(date(2023, 10, 5), 5) == date(2024, 3, 5)


def test_add_months_negative():
    assert add_months(date(2023, 10, 5), -3) == date(2023, 7, 5)


def test_add_months_clamps_to_shorter_month():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_add_months_zero_is_identity():
    d = date(2023, 10, 5)
    assert add_months(d, 0) == d


def test_weekday_is_business_day():
    assert is_business_day(date(2026, 8, 19)) is True


def test_saturday_is_not_business_day():
    assert is_business_day(date(2026, 8, 22)) is False


def test_sunday_is_not_business_day():
    assert is_business_day(date(2026, 8, 23)) is False


def test_holiday_is_not_business_day():
    holidays = {date(2026, 1, 1)}
    assert is_business_day(date(2026, 1, 1), holidays) is False


def test_recurring_holiday_is_not_business_day_any_year():
    recurring = {(12, 25)}
    assert is_business_day(date(2026, 12, 25), recurring=recurring) is False
    assert is_business_day(date(2030, 12, 25), recurring=recurring) is False


def test_next_business_day_skips_weekend():
    assert next_business_day(date(2026, 8, 22)) == date(2026, 8, 24)


def test_next_business_day_unchanged_when_already_business_day():
    d = date(2026, 8, 19)
    assert next_business_day(d) == d


def test_next_business_day_skips_weekend_and_holiday():
    holidays = {date(2026, 8, 24)}
    assert next_business_day(date(2026, 8, 22), holidays) == date(2026, 8, 25)


def test_prev_business_day_skips_weekend():
    assert prev_business_day(date(2026, 8, 22)) == date(2026, 8, 21)


def test_adjust_following_skips_holiday():
    d = date(2026, 8, 19)
    holidays = {date(2026, 8, 19)}
    assert adjust(d, "FOLLOWING", holidays) == date(2026, 8, 20)


def test_adjust_preceding_skips_weekend():
    assert adjust(date(2026, 8, 22), "PRECEDING") == date(2026, 8, 21)


def test_adjust_modified_following_stays_in_month():
    # Saturday 2026-08-15 -> next business day is Monday 2026-08-17, same month.
    assert adjust(date(2026, 8, 15), "MODIFIED_FOLLOWING") == date(2026, 8, 17)


def test_adjust_modified_following_rolls_back_at_month_end():
    # Saturday 2026-05-30 -> following would land in June, so it rolls backward instead.
    assert adjust(date(2026, 5, 30), "MODIFIED_FOLLOWING") == date(2026, 5, 29)


def test_adjust_modified_following_with_holiday_and_recurring():
    d = date(2026, 8, 22)
    holidays = {date(2026, 8, 24)}
    recurring = {(8, 25)}
    assert adjust(d, "MODIFIED_FOLLOWING", holidays, recurring) == date(2026, 8, 26)


def test_adjust_unknown_convention_raises():
    with pytest.raises(ValueError):
        adjust(date(2026, 8, 19), "MODIFIED FOLLOWING")


def test_parse_frequency_months():
    assert parse_frequency("1M") == 1
    assert parse_frequency("6M") == 6


def test_parse_frequency_years_converted_to_months():
    assert parse_frequency("1Y") == 12
    assert parse_frequency("2Y") == 24


def test_parse_frequency_lowercase_and_whitespace():
    assert parse_frequency(" 6m ") == 6


def test_parse_frequency_empty_raises():
    with pytest.raises(ValueError):
        parse_frequency("")


def test_parse_frequency_non_numeric_raises():
    with pytest.raises(ValueError):
        parse_frequency("M")


def test_parse_frequency_zero_raises():
    with pytest.raises(ValueError):
        parse_frequency("0M")


def test_parse_frequency_unsupported_unit_raises():
    with pytest.raises(ValueError):
        parse_frequency("6W")
