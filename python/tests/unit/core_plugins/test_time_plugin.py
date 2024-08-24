# Copyright (c) Microsoft. All rights reserved.

import datetime
from unittest import mock

from pytest import raises

import semantic_kernel as sk
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException

test_mock_now = datetime.datetime(2031, 1, 12, 12, 24, 56, tzinfo=datetime.timezone.utc)
test_mock_today = datetime.date(2031, 1, 12)


def test_can_be_instantiated():
    assert TimePlugin()


def test_can_be_imported():
    kernel = sk.Kernel()
    kernel.add_plugin(TimePlugin(), "time")
    assert kernel.get_plugin(plugin_name="time") is not None
    assert kernel.get_plugin(plugin_name="time").name == "time"
    assert kernel.get_function(plugin_name="time", function_name="now") is not None


def test_today():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.today() == "Sunday, 12 January, 2031"


def test_date():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.date() == "Sunday, 12 January, 2031"


def test_isodate():
    plugin = TimePlugin()

    with mock.patch("datetime.date", wraps=datetime.date) as dt:
        dt.today.return_value = test_mock_today
        assert plugin.iso_date() == "2031-01-12"


def test_now():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.now() == "Sunday, January 12, 2031 12:24 PM"


def test_days_ago():
    plugin = TimePlugin()

    with mock.patch("datetime.date", wraps=datetime.date) as dt:
        dt.today.return_value = test_mock_today
        assert plugin.days_ago(1) == "Saturday, 11 January, 2031"


def test_date_matching_last_day_name():
    plugin = TimePlugin()

    with mock.patch("datetime.date", wraps=datetime.date) as dt:
        dt.today.return_value = test_mock_today
        assert (
            plugin.date_matching_last_day_name("Friday") == "Friday, 10 January, 2031"
        )


def test_date_matching_last_day_name_fail():
    plugin = TimePlugin()

    with mock.patch("datetime.date", wraps=datetime.date) as dt:
        dt.today.return_value = test_mock_today
        with raises(FunctionExecutionException):
            plugin.date_matching_last_day_name("Non-existing-day")


def test_utc_now():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.utcnow.return_value = test_mock_now
        assert plugin.utc_now() == "Sunday, January 12, 2031 12:24 PM"


def test_time():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.time() == "12:24:56 PM"


def test_year():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.year() == "2031"


def test_month():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.month() == "January"


def test_month_number():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.month_number() == "01"


def test_day():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.day() == "12"


def test_day_of_week():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.day_of_week() == "Sunday"


def test_hour():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.hour() == "12 PM"


def test_hour_number():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.hour_number() == "12"


def test_minute():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.minute() == "24"


def test_second():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.second() == "56"


def test_time_zone_offset():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.time_zone_offset() == "+0000"


def test_time_zone_name():
    plugin = TimePlugin()

    with mock.patch("datetime.datetime", wraps=datetime.datetime) as dt:
        dt.now.return_value = test_mock_now
        assert plugin.time_zone_name() == "UTC"
