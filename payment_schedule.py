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


def adjust(
    d: date,
    convention: str,
    holidays: Optional[Set[date]] = None,
    recurring: Optional[Set[Tuple[int, int]]] = None,
) -> date:
    if convention == "FOLLOWING":
        return next_business_day(d, holidays, recurring)
    if convention == "PRECEDING":
        return prev_business_day(d, holidays, recurring)
    if convention == "MODIFIED_FOLLOWING":
        candidate = next_business_day(d, holidays, recurring)
        if candidate.month != d.month:
            return prev_business_day(d, holidays, recurring)
        return candidate
    raise ValueError("unknown convention: " + convention)


def parse_frequency(text: str) -> int:
    text = text.strip().upper()
    if not text:
        raise ValueError("frequency must not be empty")

    number, unit = text[:-1], text[-1]

    if not number.isdigit():
        raise ValueError(f"invalid frequency: {text}")

    number = int(number)
    if number <= 0:
        raise ValueError(f"frequency must be positive: {text}")

    if unit == "M":
        return number
    if unit == "Y":
        return number * 12
    raise ValueError(f"unsupported frequency unit: {unit}")


def generate_unadjusted(
    trade: date, maturity: date, months: int, generation: str = "BACKWARD"
) -> list:
    if maturity <= trade:
        raise ValueError("maturity must be after trade date")

    if generation == "BACKWARD":
        return _generate_backward(trade, maturity, months)
    if generation == "FORWARD":
        return _generate_forward(trade, maturity, months)
    raise ValueError(f"unknown generation rule: {generation}")


def _generate_backward(trade: date, maturity: date, months: int) -> list:
    dates = []
    n = 0
    while True:
        d = add_months(maturity, -months * n)
        if d <= trade:
            break
        dates.append(d)
        n += 1
    dates.reverse()  # order from trade to maturity
    return dates


def _generate_forward(trade: date, maturity: date, months: int) -> list:
    dates = []
    n = 1
    while True:
        d = add_months(trade, months * n)
        if d >= maturity:
            break
        dates.append(d)
        n += 1
    dates.append(maturity)
    return dates


def build_schedule(
    trade: date,
    maturity: date,
    frequency: str,
    convention: str,
    holidays: Optional[Set[date]] = None,
    recurring: Optional[Set[Tuple[int, int]]] = None,
    generation: str = "BACKWARD",
) -> Tuple[list, list]:
    months = parse_frequency(frequency)
    unadjusted = generate_unadjusted(trade, maturity, months, generation)
    adjusted = [adjust(d, convention, holidays, recurring) for d in unadjusted]
    return unadjusted, adjusted
