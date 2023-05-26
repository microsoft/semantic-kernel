import datetime
from unittest import mock

import semantic_kernel as sk
from semantic_kernel.core_skills.time_skill import TimeSkill

test_mock_now = datetime.datetime(2031, 1, 12, 12, 24, 56, tzinfo=datetime.timezone.utc)
test_mock_today = datetime.date(2031, 1, 12)


def test_can_be_instantiated():
    assert TimeSkill()


def test_can_be_imported():
    kernel = sk.Kernel()
    assert kernel.import_skill(TimeSkill(), "time")
    assert kernel.skills.has_native_function("time", "now")


def test_date():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.date() == "Sunday, 12 January, 2031"


def test_now():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.now() == "Sunday, January 12, 2031 12:24 PM"


def test_days_ago():
    skill = TimeSkill()

    with mock.patch("datetime.date", wraps=datetime.date) as dt:
        dt.today.return_value = test_mock_today
        assert skill.days_ago(1) == "Saturday, 11 January, 2031"


def test_date_matching_last_day_name():
    skill = TimeSkill()

    with mock.patch("datetime.date", wraps=datetime.date) as dt:
        dt.today.return_value = test_mock_today
        assert skill.date_matching_last_day_name("Friday") == "Friday, 10 January, 2031"


def test_utc_now():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.utcnow.return_value = test_mock_now
        assert skill.utc_now() == "Sunday, January 12, 2031 12:24 PM"


def test_time():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.time() == "12:24:56 PM"


def test_year():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.year() == "2031"


def test_month():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.month() == "January"


def test_month_number():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.month_number() == "01"


def test_day():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.day() == "12"


def test_day_of_week():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.day_of_week() == "Sunday"


def test_hour():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.hour() == "12 PM"


def test_minute():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.minute() == "24"


def test_second():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.second() == "56"


def test_time_zone_offset():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.time_zone_offset() == "+0000"


def test_time_zone_name():
    skill = TimeSkill()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert skill.time_zone_name() == "UTC"
