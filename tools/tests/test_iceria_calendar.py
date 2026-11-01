"""The calendar converter: two real months are one in-world year, from the month of launch."""

import calendar
import json
from datetime import datetime, timedelta

import iceria_calendar as cal
import pytest

START = (2026, 11)


@pytest.mark.parametrize(
    "real, expected",
    [
        (datetime(2026, 11, 1), "1 January 2000"),
        (datetime(2026, 12, 1), "2 July 2000"),  # halfway: day 184 of a leap year
        (datetime(2027, 1, 1), "1 January 2001"),
    ],
)
def test_a_real_moment_gives_the_in_world_date(real, expected):
    assert cal.format_date(cal.in_world_date(real, START)) == expected


def test_before_the_start_there_is_no_in_world_date():
    assert cal.in_world_date(datetime(2026, 10, 31, 23, 59), START) is None


@pytest.mark.parametrize(
    "date, real",
    [
        ("1 January 2000", datetime(2026, 11, 1)),
        ("2 July 2000", datetime(2026, 12, 1)),
        ("1 January 2001", datetime(2027, 1, 1)),
    ],
)
def test_an_in_world_date_gives_the_real_moment_it_begins(date, real):
    assert cal.real_start(cal.parse_date(date), START) == real


def test_the_reverse_lands_on_the_first_minute_of_every_day_for_four_years():
    for year in range(2000, 2004):
        for month in range(1, 13):
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                begins = cal.real_start((year, month, day), START)
                assert cal.in_world_date(begins, START) == (year, month, day)
                assert cal.in_world_date(begins - timedelta(minutes=1), START) != (year, month, day)


def test_a_badly_written_date_is_refused_with_the_form_to_use():
    with pytest.raises(ValueError, match="14 March 2001"):
        cal.parse_date("March 14, 2001")


def kit(tmp_path, start):
    (tmp_path / "VERSION.json").write_text(json.dumps({"calendar_start": start}), "utf-8")
    return tmp_path


def test_cli_reads_the_start_from_version_json(tmp_path, capsys):
    assert cal.main(["--real", "2026-12-01"], kit(tmp_path, "2026-11")) == 0
    assert capsys.readouterr().out.strip() == "2 July 2000"


def test_cli_turns_an_in_world_date_into_utc(tmp_path, capsys):
    assert cal.main(["--in-world", "1 January 2001"], kit(tmp_path, "2026-11")) == 0
    assert capsys.readouterr().out.strip() == "1 January 2001 begins at 2027-01-01 00:00 UTC"


def test_cli_before_launch_says_the_calendar_has_not_started(tmp_path, capsys):
    assert cal.main([], kit(tmp_path, None)) == 0
    out = capsys.readouterr().out
    assert "has not started" in out and "2000 (MoS 5.1)" in out


def test_cli_start_flag_overrides_version_json(tmp_path, capsys):
    assert cal.main(["--start", "2027-01", "--real", "2027-01-01"], kit(tmp_path, None)) == 0
    assert capsys.readouterr().out.strip() == "1 January 2000"
