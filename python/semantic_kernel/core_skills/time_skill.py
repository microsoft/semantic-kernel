# Copyright (c) Microsoft. All rights reserved.

import datetime

from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition import sk_function


class TimeSkill(PydanticField):
    """
    Description: TimeSkill provides a set of functions
                 to get the current time and date.

    Usage:
        kernel.import_skill(TimeSkill(), skill_name="time")

    Examples:
        {{time.date}}            => Sunday, 12 January, 2031
        {{time.today}}           => Sunday, 12 January, 2031
        {{time.iso_date}}        => 2031-01-12
        {{time.now}}             => Sunday, January 12, 2031 9:15 PM
        {{time.utcNow}}          => Sunday, January 13, 2031 5:15 AM
        {{time.time}}            => 09:15:07 PM
        {{time.year}}            => 2031
        {{time.month}}           => January
        {{time.monthNumber}}     => 01
        {{time.day}}             => 12
        {{time.dayOfWeek}}       => Sunday
        {{time.hour}}            => 9 PM
        {{time.hourNumber}}      => 21
        {{time.days_ago $days}} => Sunday, 7 May, 2023
        {{time.last_matching_day $dayName}} => Sunday, 7 May, 2023
        {{time.minute}}          => 15
        {{time.minutes}}         => 15
        {{time.second}}          => 7
        {{time.seconds}}         => 7
        {{time.timeZoneOffset}}  => -0800
        {{time.timeZoneName}}    => PST
    """

    @sk_function(description="Get the current date.")
    def date(self) -> str:
        """
        Get the current date

        Example:
            {{time.date}} => Sunday, 12 January, 2031
        """
        now = datetime.datetime.now()
        return now.strftime("%A, %d %B, %Y")

    @sk_function(description="Get the current date.")
    def today(self) -> str:
        """
        Get the current date

        Example:
            {{time.today}} => Sunday, 12 January, 2031
        """
        return self.date()

    @sk_function(description="Get the current date in iso format.")
    def iso_date(self) -> str:
        """
        Get the current date in iso format

        Example:
            {{time.iso_date}} => 2031-01-12
        """
        today = datetime.date.today()
        return today.isoformat()

    @sk_function(description="Get the current date and time in the local time zone")
    def now(self) -> str:
        """
        Get the current date and time in the local time zone"

        Example:
            {{time.now}} => Sunday, January 12, 2031 9:15 PM
        """
        now = datetime.datetime.now()
        return now.strftime("%A, %B %d, %Y %I:%M %p")

    @sk_function(description="Get the current date and time in UTC", name="utcNow")
    def utc_now(self) -> str:
        """
        Get the current date and time in UTC

        Example:
            {{time.utcNow}} => Sunday, January 13, 2031 5:15 AM
        """
        now = datetime.datetime.utcnow()
        return now.strftime("%A, %B %d, %Y %I:%M %p")

    @sk_function(description="Get the current time in the local time zone")
    def time(self) -> str:
        """
        Get the current time in the local time zone

        Example:
            {{time.time}} => 09:15:07 PM
        """
        now = datetime.datetime.now()
        return now.strftime("%I:%M:%S %p")

    @sk_function(description="Get the current year")
    def year(self) -> str:
        """
        Get the current year

        Example:
            {{time.year}} => 2031
        """
        now = datetime.datetime.now()
        return now.strftime("%Y")

    @sk_function(description="Get the current month")
    def month(self) -> str:
        """
        Get the current month

        Example:
            {{time.month}} => January
        """
        now = datetime.datetime.now()
        return now.strftime("%B")

    @sk_function(description="Get the current month number")
    def month_number(self) -> str:
        """
        Get the current month number

        Example:
            {{time.monthNumber}} => 01
        """
        now = datetime.datetime.now()
        return now.strftime("%m")

    @sk_function(description="Get the current day")
    def day(self) -> str:
        """
        Get the current day of the month

        Example:
            {{time.day}} => 12
        """
        now = datetime.datetime.now()
        return now.strftime("%d")

    @sk_function(description="Get the current day of the week", name="dayOfWeek")
    def day_of_week(self) -> str:
        """
        Get the current day of the week

        Example:
            {{time.dayOfWeek}} => Sunday
        """
        now = datetime.datetime.now()
        return now.strftime("%A")

    @sk_function(description="Get the current hour")
    def hour(self) -> str:
        """
        Get the current hour

        Example:
            {{time.hour}} => 9 PM
        """
        now = datetime.datetime.now()
        return now.strftime("%I %p")

    @sk_function(description="Get the current hour number", name="hourNumber")
    def hour_number(self) -> str:
        """
        Get the current hour number

        Example:
            {{time.hourNumber}} => 21
        """
        now = datetime.datetime.now()
        return now.strftime("%H")

    @sk_function(description="Get the current minute")
    def minute(self) -> str:
        """
        Get the current minute

        Example:
            {{time.minute}} => 15
        """
        now = datetime.datetime.now()
        return now.strftime("%M")

    @sk_function(
        description="Get the date of offset from today by a provided number of days"
    )
    def days_ago(self, days: str) -> str:
        """
        Get the date a provided number of days in the past

        params:
            days: The number of days to offset from today
        returns:
            The date of the offset day.

        Example:
             SKContext["input"] = "3"
             {{time.days_ago $input}} => Sunday, 7 May, 2023
        """
        d = datetime.date.today() - datetime.timedelta(days=int(days))
        return d.strftime("%A, %d %B, %Y")

    @sk_function(
        description="""Get the date of the last day matching the supplied week day name in English.
        Example: Che giorno era 'Martedi' scorso -> dateMatchingLastDayName 'Tuesday' => Tuesday,
        16 May, 2023"""
    )
    def date_matching_last_day_name(self, day_name: str) -> str:
        """
        Get the date of the last day matching the supplied day name

        params:
            day_name: The day name to match with.
        returns:
            The date of the matching day.

        Example:
             SKContext["input"] = "Sunday"
             {{time.date_matching_last_day_name $input}} => Sunday, 7 May, 2023
        """
        d = datetime.date.today()
        for i in range(1, 8):
            d = d - datetime.timedelta(days=1)
            if d.strftime("%A") == day_name:
                return d.strftime("%A, %d %B, %Y")
        raise ValueError("day_name is not recognized")

    @sk_function(description="Get the seconds on the current minute")
    def second(self) -> str:
        """
        Get the seconds on the current minute

        Example:
            {{time.second}} => 7
        """
        now = datetime.datetime.now()
        return now.strftime("%S")

    @sk_function(description="Get the current time zone offset", name="timeZoneOffset")
    def time_zone_offset(self) -> str:
        """
        Get the current time zone offset

        Example:
            {{time.timeZoneOffset}} => -08:00
        """
        now = datetime.datetime.now()
        return now.strftime("%z")

    @sk_function(description="Get the current time zone name", name="timeZoneName")
    def time_zone_name(self) -> str:
        """
        Get the current time zone name

        Example:
            {{time.timeZoneName}} => PST
        """
        now = datetime.datetime.now()
        return now.strftime("%Z")
