from datetime import date

from payment_schedule import days_in_month, add_months


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
