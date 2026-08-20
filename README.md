# Business Day Payment Schedule

Generates payment dates between a trade date and a maturity date, and adjusts each
date to a valid business day. Python standard library only (`datetime`), no
external date or schedule libraries.

## Running it

```
python payment_schedule.py example.json
pytest
```

## Input format

```json
{
  "tradeDate": "2026-01-15",
  "maturityDate": "2027-01-15",
  "frequency": "6M",
  "businessDayConvention": "MODIFIED_FOLLOWING",
  "holidays": ["2026-01-01", "2026-12-25"],
  "recurringHolidays": ["01-01", "12-25"],
  "generation": "BACKWARD"
}
```

| Field | Values | Notes |
|---|---|---|
| `tradeDate` | ISO date | Must be before maturity |
| `maturityDate` | ISO date | Always a payment date |
| `frequency` | e.g. `1M`, `3M`, `6M`, `1Y` | Months or years |
| `businessDayConvention` | `FOLLOWING`, `MODIFIED_FOLLOWING`, `PRECEDING` | |
| `holidays` | list of ISO dates | Optional, defaults to empty |
| `recurringHolidays` | list of `MM-DD` | Optional, e.g. New Year's every year |
| `generation` | `BACKWARD`, `FORWARD` | Optional, defaults to `BACKWARD` |

## Output format

```json
{
  "unadjustedDates": ["2026-07-15", "2027-01-15"],
  "adjustedDates": ["2026-07-15", "2027-01-15"]
}
```

Both schedules are returned: the unadjusted one is the theoretical schedule, the
adjusted one is where payments actually settle.

## Design decisions

- Dates are generated backwards from maturity, so the stub falls at the start of the schedule. `generation: FORWARD` puts it at the end instead.
- Each date is computed as `maturity - n * frequency`, not by adding to the previous date, which would drift after a month-end clamp.
- Generation and adjustment are separate: the generator knows nothing about holidays, and the adjustment knows nothing about schedules.
- Holidays are a set, so combining calendars is a union — a payment across two jurisdictions only settles when both markets are open.

## Files

- `payment_schedule.py` — the implementation, and a CLI entry point (`python payment_schedule.py <input.json>`)
- `test_payment_schedule.py` — pytest test suite
- `Notebook/exploration.ipynb` — the scratch notebook used to work out the logic before it was ported into the modules above

## AI usage declaration

I worked out the logic myself first, in `Notebook/exploration.ipynb` (month
arithmetic, business day checks, the adjustment conventions, schedule
generation). Claude Code was then used to help port that notebook into
`payment_schedule.py` and `test_payment_schedule.py`: cleaning up the code,
adding type hints and error handling, building the JSON input/output layer,
and reviewing edge cases. All logic was verified by running the test suite
after each step.
