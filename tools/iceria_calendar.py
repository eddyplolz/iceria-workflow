"""Turn a real date into Iceria's in-world date, and back (World Standards section 5).

    python tools/iceria_calendar.py                            today's in-world date
    python tools/iceria_calendar.py --real 2027-01-15          the in-world date at that moment
    python tools/iceria_calendar.py --in-world "14 March 2001" the real moment that date begins

Two real months are one in-world year, and year 2000 begins when the calendar started: a real month
(its 1st) or a real day, which VERSION.json records as calendar_start ("YYYY-MM" or "YYYY-MM-DD",
copied from the wiki's Module:Iceria date). Real times are UTC. The sum is the one Module:Iceria
date does on the wiki.
"""

import argparse
import calendar
import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import kit_python  # noqa: F401  stops on Python < 3.10

KIT = Path(__file__).resolve().parents[1]
REAL_MONTHS_PER_YEAR = 2
MONTHS = calendar.month_name[1:]


def _year_days(year: int) -> int:
    return 366 if calendar.isleap(year) else 365


def in_world_date(
    real: datetime, start: tuple[int, int] | tuple[int, int, int]
) -> tuple[int, int, int] | None:
    """The in-world (year, month, day) at a real UTC time, or None before the calendar began.

    start is (year, month), meaning the 1st of that month, or (year, month, day)."""
    start_year, start_month, start_day = (*start, 1) if len(start) == 2 else start
    if not 1 <= start_month <= 12:
        raise ValueError(f"start month {start_month} is not 1 to 12")
    start_month_days = calendar.monthrange(start_year, start_month)[1]
    if not 1 <= start_day <= start_month_days:
        raise ValueError(f"start day {start_day} is not 1 to {start_month_days}")
    month_days = calendar.monthrange(real.year, real.month)[1]
    in_month = (real.day - 1 + real.hour / 24 + real.minute / 1440) / month_days
    # Whole months gone by since the start, plus the part-month as its share of that month's
    # days. The whole months stay an integer: folding them into the float drifts a day boundary.
    elapsed = (real.year * 12 + real.month) - (start_year * 12 + start_month)
    part = in_month - (start_day - 1) / start_month_days
    if part < 0:
        elapsed, part = elapsed - 1, part + 1
    if elapsed < 0:
        return None
    year = 2000 + elapsed // REAL_MONTHS_PER_YEAR
    share = (elapsed % REAL_MONTHS_PER_YEAR + part) / REAL_MONTHS_PER_YEAR
    n = int(share * _year_days(year))
    month = 1
    while n >= calendar.monthrange(year, month)[1]:
        n -= calendar.monthrange(year, month)[1]
        month += 1
    return year, month, n + 1


def real_start(
    date: tuple[int, int, int], start: tuple[int, int] | tuple[int, int, int]
) -> datetime:
    """The first real UTC minute at which in_world_date gives `date`."""
    year, month, day = date
    start_year, start_month, start_day = (*start, 1) if len(start) == 2 else start
    n = sum(calendar.monthrange(year, m)[1] for m in range(1, month)) + day - 1
    months = (year - 2000) * REAL_MONTHS_PER_YEAR + n / _year_days(year) * REAL_MONTHS_PER_YEAR
    # Counted from the 1st of the start month, so a start day adds its share of that month.
    months += (start_day - 1) / calendar.monthrange(start_year, start_month)[1]
    whole = int(months)
    total = start_year * 12 + start_month - 1 + whole
    first = datetime(total // 12, total % 12 + 1, 1)
    month_days = calendar.monthrange(first.year, first.month)[1]
    # Rounded up: the forward sum counts whole minutes, so the day begins on the next one.
    minutes = math.ceil(round((months - whole) * month_days * 1440, 6))
    return first + timedelta(minutes=minutes)


def format_date(date: tuple[int, int, int]) -> str:
    """'17 March 2000', as the Manual of Style writes dates."""
    year, month, day = date
    return f"{day} {MONTHS[month - 1]} {year}"


def parse_date(text: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"\s*(\d{1,2}) ([A-Za-z]+) (\d{4})\s*", text)
    month = m and m.group(2).capitalize()
    if not m or month not in MONTHS:
        raise ValueError(f"write the date as day, month, year: 14 March 2001, not {text!r}")
    year, mon, day = int(m.group(3)), MONTHS.index(month) + 1, int(m.group(1))
    if not 1 <= day <= calendar.monthrange(year, mon)[1]:
        raise ValueError(f"{text!r}: {month} {year} has no day {day}")
    return year, mon, day


def _start(text: str | None) -> tuple[int, int] | tuple[int, int, int] | None:
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", text or "")
    ok = m and 1 <= int(m.group(2)) <= 12
    if ok and m.group(3):
        ok = 1 <= int(m.group(3)) <= calendar.monthrange(int(m.group(1)), int(m.group(2)))[1]
    if text and not ok:
        raise ValueError(
            f"the start is a real month or day written YYYY-MM or YYYY-MM-DD, not {text!r}"
        )
    if not m:
        return None
    return tuple(int(g) for g in m.groups() if g)


def main(argv: list[str] | None = None, kit: Path = KIT) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--real", help="a real UTC moment: YYYY-MM-DD or 'YYYY-MM-DD HH:MM'")
    group.add_argument("--in-world", help="an in-world date: '14 March 2001'")
    ap.add_argument(
        "--start", help="the real month or day the calendar started, YYYY-MM or YYYY-MM-DD"
    )
    args = ap.parse_args(argv)
    try:
        version = json.loads((kit / "VERSION.json").read_text(encoding="utf-8"))
        start = _start(args.start or version.get("calendar_start"))
        if start is None:
            print(
                "The in-world calendar has not started, so figures are given for 2000 (MoS 5.1). "
                "Run python tools/refresh_canon.py after launch to copy its start."
            )
            return 0
        if args.in_world:
            date = parse_date(args.in_world)
            begins = real_start(date, start)
            print(f"{format_date(date)} begins at {begins:%Y-%m-%d %H:%M} UTC")
            return 0
        if args.real:
            real = datetime.fromisoformat(args.real)
        else:
            real = datetime.now(timezone.utc).replace(tzinfo=None)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    date = in_world_date(real, start)
    if date is None:
        print(
            f"{real:%Y-%m-%d} is before the calendar started ({'-'.join(f'{v:02d}' for v in start)})"
        )
        return 0
    print(format_date(date))
    return 0


if __name__ == "__main__":
    sys.exit(main())
