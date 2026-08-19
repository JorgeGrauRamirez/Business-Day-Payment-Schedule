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
    generate_unadjusted,
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


def test_generate_unadjusted_backward_regular_schedule():
    result = generate_unadjusted(date(2026, 8, 19), date(2027, 8, 22), 6, "BACKWARD")
    assert result == [date(2026, 8, 22), date(2027, 2, 22), date(2027, 8, 22)]


def test_generate_unadjusted_trade_date_not_included():
    trade = date(2026, 8, 19)
    dates = generate_unadjusted(trade, date(2027, 8, 19), 6, "BACKWARD")
    assert trade not in dates


def test_generate_unadjusted_backward_and_forward_differ_on_stub_position():
    trade, maturity = date(2026, 1, 15), date(2027, 3, 15)
    back = generate_unadjusted(trade, maturity, 6, "BACKWARD")
    fwd = generate_unadjusted(trade, maturity, 6, "FORWARD")
    assert len(back) == len(fwd) == 3
    assert back[0] == date(2026, 3, 15)  # long stub at the start
    assert fwd[0] == date(2026, 7, 15)  # long stub at the end


def test_generate_unadjusted_forward_always_ends_on_maturity():
    result = generate_unadjusted(date(2026, 1, 15), date(2027, 3, 15), 6, "FORWARD")
    assert result[-1] == date(2027, 3, 15)


def test_generate_unadjusted_maturity_before_trade_raises():
    with pytest.raises(ValueError):
        generate_unadjusted(date(2027, 1, 15), date(2026, 1, 15), 6, "BACKWARD")


def test_generate_unadjusted_maturity_equal_trade_raises():
    d = date(2026, 1, 15)
    with pytest.raises(ValueError):
        generate_unadjusted(d, d, 6, "BACKWARD")


def test_generate_unadjusted_unknown_generation_raises():
    with pytest.raises(ValueError):
        generate_unadjusted(date(2026, 1, 15), date(2027, 1, 15), 6, "SIDEWAYS")
