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
    build_schedule,
    parse_holidays,
    parse_recurring_holidays,
    parse_request,
    format_schedule,
    run_schedule,
)


def test_days_in_month_regular():
    assert days_in_month(2026, 1) == 31
    assert days_in_month(2026, 4) == 30


def test_days_in_month_february():
    assert days_in_month(2024, 2) == 29
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


def test_parse_frequency():
    assert parse_frequency("1M") == 1 # monthly
    assert parse_frequency("3M") == 3 #quarterly
    assert parse_frequency("6M") == 6 # half yearly
    assert parse_frequency("1Y") == 12 # year
    assert parse_frequency("2Y") == 24
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


def test_build_schedule_returns_both_lists_same_length():
    unadjusted, adjusted = build_schedule(
        date(2026, 1, 15), date(2027, 1, 15), "6M", "MODIFIED_FOLLOWING"
    )
    assert len(unadjusted) == len(adjusted) == 2
    for u, a in zip(unadjusted, adjusted):
        assert abs((a - u).days) <= 4


def test_build_schedule_applies_holidays():
    unadjusted, adjusted = build_schedule(
        date(2026, 1, 15),
        date(2027, 1, 15),
        "6M",
        "FOLLOWING",
        holidays={date(2027, 1, 15)},
    )
    assert unadjusted[-1] == date(2027, 1, 15)
    assert adjusted[-1] == date(2027, 1, 18)


def test_build_schedule_combines_multiple_holiday_calendars():
    calendar_dk = {date(2026, 6, 5)}
    calendar_us = {date(2026, 7, 3)}
    combined = calendar_dk | calendar_us

    unadjusted, adjusted = build_schedule(
        date(2026, 1, 5), date(2026, 8, 5), "1M", "FOLLOWING", holidays=combined
    )
    assert date(2026, 6, 5) not in adjusted
    assert date(2026, 7, 3) not in adjusted


def test_parse_holidays_converts_iso_strings_to_dates():
    result = parse_holidays(["2026-01-01", "2026-12-25"])
    assert result == {date(2026, 1, 1), date(2026, 12, 25)}


def test_parse_holidays_empty_list():
    assert parse_holidays([]) == set()


def test_parse_recurring_holidays_converts_mm_dd_to_tuples():
    result = parse_recurring_holidays(["01-01", "12-25"])
    assert result == {(1, 1), (12, 25)}


def test_parse_recurring_holidays_rejects_bad_format():
    with pytest.raises(ValueError):
        parse_recurring_holidays(["2026-01-01"])  # full date, not MM-DD


def test_parse_recurring_holidays_rejects_invalid_calendar_date():
    with pytest.raises(ValueError):
        parse_recurring_holidays(["02-30"])  # Feb 30 doesn't exist


def test_parse_recurring_holidays_rejects_invalid_month():
    with pytest.raises(ValueError):
        parse_recurring_holidays(["13-01"])


def test_parse_request_full_payload():
    data = {
        "tradeDate": "2026-01-15",
        "maturityDate": "2027-01-15",
        "frequency": "6M",
        "businessDayConvention": "MODIFIED_FOLLOWING",
        "holidays": ["2026-01-01"],
        "recurringHolidays": ["12-25"],
    }
    parsed = parse_request(data)
    assert parsed["trade"] == date(2026, 1, 15)
    assert parsed["maturity"] == date(2027, 1, 15)
    assert parsed["frequency"] == "6M"
    assert parsed["convention"] == "MODIFIED_FOLLOWING"
    assert parsed["holidays"] == {date(2026, 1, 1)}
    assert parsed["recurring"] == {(12, 25)}
    assert parsed["generation"] == "BACKWARD"


def test_parse_request_defaults_optional_fields():
    data = {
        "tradeDate": "2026-01-15",
        "maturityDate": "2027-01-15",
        "frequency": "6M",
        "businessDayConvention": "FOLLOWING",
    }
    parsed = parse_request(data)
    assert parsed["holidays"] == set()
    assert parsed["recurring"] == set()
    assert parsed["generation"] == "BACKWARD"


def test_parse_request_missing_required_field_raises():
    data = {
        "tradeDate": "2026-01-15",
        "maturityDate": "2027-01-15",
        "frequency": "6M",
        # businessDayConvention missing
    }
    with pytest.raises(ValueError):
        parse_request(data)


def test_format_schedule_converts_dates_to_iso_strings():
    result = format_schedule([date(2026, 2, 15)], [date(2026, 2, 16)])
    assert result == {
        "unadjustedDates": ["2026-02-15"],
        "adjustedDates": ["2026-02-16"],
    }


def test_run_schedule_end_to_end():
    data = {
        "tradeDate": "2026-01-15",
        "maturityDate": "2027-01-15",
        "frequency": "6M",
        "businessDayConvention": "FOLLOWING",
        "holidays": ["2027-01-15"],
    }
    result = run_schedule(data)
    assert result["unadjustedDates"][-1] == "2027-01-15"
    assert result["adjustedDates"][-1] == "2027-01-18"
