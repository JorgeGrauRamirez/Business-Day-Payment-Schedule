from datetime import date, timedelta
from typing import Optional, Set, Tuple


def days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - timedelta(days=1)).day


def add_months(d: date, n: int) -> date:
    total = d.month - 1 + n
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, days_in_month(year, month))
    return date(year, month, day)


def is_business_day(
    d: date,
    holidays: Optional[Set[date]] = None,
    recurring: Optional[Set[Tuple[int, int]]] = None,
) -> bool:
    if holidays is None:
        holidays = set()
    if recurring is None:
        recurring = set()
    if d.weekday() >= 5:
        return False
    if d in holidays:
        return False
    if (d.month, d.day) in recurring:
        return False
    return True


def next_business_day(
    d: date,
    holidays: Optional[Set[date]] = None,
    recurring: Optional[Set[Tuple[int, int]]] = None,
) -> date:
    while not is_business_day(d, holidays, recurring):
        d = d + timedelta(days=1)
    return d


def prev_business_day(
    d: date,
    holidays: Optional[Set[date]] = None,
    recurring: Optional[Set[Tuple[int, int]]] = None,
) -> date:
    while not is_business_day(d, holidays, recurring):
        d = d - timedelta(days=1)
    return d
