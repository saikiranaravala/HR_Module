"""Calendar-month arithmetic. `months * 30` drifts (≈10 days over a biennial
compliance anniversary) — statutory windows use real calendar months, with the
day clamped to the target month's length (Jan 31 + 1 month = Feb 28/29)."""
import calendar
from datetime import date


def add_months(start: date, months: int) -> date:
    month_index = start.year * 12 + (start.month - 1) + months
    year, month = divmod(month_index, 12)
    month += 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
