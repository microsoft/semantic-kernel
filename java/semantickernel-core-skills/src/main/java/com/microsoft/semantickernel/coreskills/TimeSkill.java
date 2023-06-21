package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;

import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;
import java.time.format.TextStyle;
import java.util.Locale;

public class TimeSkill {
    /**
     * Get the current date.
     *
     * @return The current date.
     */
    @DefineSKFunction(name = "date", description = "Get the current date")
    public String date() {
        return DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(ZonedDateTime.now());
    }

    /**
     * Get the current time.
     *
     * @return The current time.
     */
    @DefineSKFunction(name = "time", description = "Get the current time")
    public String time() {
        return DateTimeFormatter.ofPattern("hh:mm:ss a").format(ZonedDateTime.now());
    }

    /**
     * Get the current UTC date and time.
     *
     * @return The current UTC date and time.
     */
    @DefineSKFunction(name = "utcNow", description = "Get the current UTC date and time")
    public String utcNow() {
        return DateTimeFormatter.ofPattern("EEEE, MMMM dd, yyyy h:mm a").format(ZonedDateTime.now().withZoneSameInstant(ZoneOffset.UTC));
    }

    /**
     * Get the current date (alias for date() method).
     *
     * @return The current date.
     */
    @DefineSKFunction(name = "today", description = "Get the current date")
    public String today() {
        return date();
    }

    /**
     * Get the current date and time in the local time zone.
     *
     * @return The current date and time in the local time zone.
     */
    @DefineSKFunction(name = "now", description = "Get the current date and time in the local time zone")
    public String now() {
        return DateTimeFormatter.ofPattern("EEEE, MMMM dd, yyyy h:mm a").format(ZonedDateTime.now());
    }


    /**
     * Get the current year.
     *
     * @return The current year.
     */
    @DefineSKFunction(name = "year", description = "Get the current year")
    public String year() {
        return DateTimeFormatter.ofPattern("yyyy").format(ZonedDateTime.now());
    }

    /**
     * Get the current month name.
     *
     * @return The current month name.
     */
    @DefineSKFunction(name = "month", description = "Get the current month name")
    public String month() {
        return DateTimeFormatter.ofPattern("MMMM").format(ZonedDateTime.now());
    }

    /**
     * Get the current month number.
     *
     * @return The current month number.
     */
    @DefineSKFunction(name = "monthNumber", description = "Get the current month number")
    public String monthNumber() {
        return DateTimeFormatter.ofPattern("MM").format(ZonedDateTime.now());
    }

    /**
     * Get the current day of the month.
     *
     * @return The current day of the month.
     */
    @DefineSKFunction(name = "day", description = "Get the current day of the month")
    public String day() {
        return DateTimeFormatter.ofPattern("dd").format(ZonedDateTime.now());
    }

    /**
     * Get the current day of the week.
     *
     * @return The current day of the week.
     */
    @DefineSKFunction(name = "dayOfWeek", description = "Get the current day of the week")
    public String dayOfWeek() {
        return DateTimeFormatter.ofPattern("EEEE").format(ZonedDateTime.now());
    }

    /**
     * Get the current clock hour.
     *
     * @return The current clock hour.
     */
    @DefineSKFunction(name = "hour", description = "Get the current clock hour")
    public String hour() {
        return DateTimeFormatter.ofPattern("h a").format(ZonedDateTime.now());
    }

    /**
     * Get the current clock 24-hour number.
     *
     * @return The current clock 24-hour number.
     */
    @DefineSKFunction(name = "hourNumber", description = "Get the current clock 24-hour number")
    public String hourNumber() {
        return DateTimeFormatter.ofPattern("HH").format(ZonedDateTime.now());
    }

    /**
     * Get the minutes on the current hour.
     *
     * @return The minutes on the current hour.
     */
    @DefineSKFunction(name = "minute", description = "Get the minutes on the current hour")
    public String minute() {
        return DateTimeFormatter.ofPattern("mm").format(ZonedDateTime.now());
    }

    /**
     * Get the seconds on the current minute.
     *
     * @return The seconds on the current minute.
     */
    @DefineSKFunction(name = "second", description = "Get the seconds on the current minute")
    public String second() {
        return DateTimeFormatter.ofPattern("ss").format(ZonedDateTime.now());
    }

    /**
     * Get the local time zone offset from UTC.
     *
     * @return The local time zone offset from UTC.
     */
    @DefineSKFunction(name = "timeZoneOffset", description = "Get the local time zone offset from UTC")
    public String timeZoneOffset() {
        return DateTimeFormatter.ofPattern("XXX").format(ZonedDateTime.now());
    }

    /**
     * Get the local time zone name.
     *
     * @return The local time zone name.
     */
    @DefineSKFunction(name = "timeZoneName", description = "Get the local time zone name")
    public String timeZoneName() {
        ZoneId zoneId = ZoneId.systemDefault();
        return zoneId.getDisplayName(TextStyle.SHORT, Locale.getDefault());
    }
}
