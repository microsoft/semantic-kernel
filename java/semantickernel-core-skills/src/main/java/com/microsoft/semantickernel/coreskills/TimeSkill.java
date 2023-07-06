// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;

import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.TextStyle;
import java.util.Locale;

/**
 * Description: TimeSkill provides a set of functions to get the current time and date.
 *
 * <p>Usage: kernel.importSkill(new TimeSkill(), "time");
 *
 * <p>Examples:
 *
 * <p>{{time.date}} => Sunday, 12 January, 2031
 *
 * <p>{{time.today}} => Sunday, 12 January, 2031
 *
 * <p>{{time.now}} => Sunday, January 12, 2031 9:15 PM
 *
 * <p>{{time.utcNow}} => Sunday, January 13, 2031 5:15 AM
 *
 * <p>{{time.time}} => 09:15:07 PM
 *
 * <p>{{time.year}} => 2031
 *
 * <p>{{time.month}} => January
 *
 * <p>{{time.monthNumber}} => 01
 *
 * <p>{{time.day}} => 12
 *
 * <p>{{time.dayOfWeek}} => Sunday
 *
 * <p>{{time.hour}} => 9 PM
 *
 * <p>{{time.hourNumber}} => 21
 *
 * <p>{{time.days_ago $days}} => Sunday, 7 May, 2023
 *
 * <p>{{time.last_matching_day $dayName}} => Sunday, 7 May, 2023
 *
 * <p>{{time.minute}} => 15
 *
 * <p>{{time.second}} => 7
 *
 * <p>{{time.timeZoneOffset}} => -08:00
 *
 * <p>{{time.timeZoneName}} => Pacific Time
 */
public class TimeSkill {

    public static final String DAY_MONTH_DAY_YEAR = "EEEE, MMMM d, yyyy";

    /**
     * Get the current date.
     *
     * <p>Example: {{time.date}} => Sunday, January 12, 2025
     *
     * @return The current date.
     */
    @DefineSKFunction(name = "date", description = "Get the current date")
    public String date() {
        // Example: Sunday, 12 January, 2025
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR).format(ZonedDateTime.now());
    }

    /**
     * Get the current time.
     *
     * <p>Example: {{time.time}} => 9:15:00 AM
     *
     * @return The current time.
     */
    @DefineSKFunction(name = "time", description = "Get the current time")
    public String time() {
        // Example: 09:15:07 PM
        return DateTimeFormatter.ofPattern("hh:mm:ss a").format(ZonedDateTime.now());
    }

    /**
     * Get the current UTC date and time.
     *
     * <p>Example: {{time.utcNow}} => Sunday, January 13, 2025 5:15 AM
     *
     * @return The current UTC date and time.
     */
    @DefineSKFunction(name = "utcNow", description = "Get the current UTC date and time")
    public String utcNow() {
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR + " h:mm a")
                .format(ZonedDateTime.now().withZoneSameInstant(ZoneOffset.UTC));
    }

    /**
     * Get the current date (alias for date() method).
     *
     * <p>Example: {{time.today}} => Sunday, January 12, 2025
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
     * <p>Example: {{time.now}} => Sunday, January 12, 2025 9:15 AM
     *
     * @return The current date and time in the local time zone.
     */
    @DefineSKFunction(
            name = "now",
            description = "Get the current date and time in the local time zone")
    public String now() {
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR + " h:mm a")
                .format(ZonedDateTime.now());
    }

    /**
     * Get the current year.
     *
     * <p>Example: {{time.year}} => 2025
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
     * <p>Example: {{time.month}} => January
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
     * <p>Example: {{time.monthNumber}} => 01
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
     * <p>Example: {{time.day}} => 12
     *
     * @return The current day of the month.
     */
    @DefineSKFunction(name = "day", description = "Get the current day of the month")
    public String day() {
        return DateTimeFormatter.ofPattern("d").format(ZonedDateTime.now());
    }

    /**
     * Get the current day of the week.
     *
     * <p>Example: {{time.dayOfWeek}} => Sunday
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
     * <p>Example: {{time.hour}} => 9 AM
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
     * <p>Example: {{time.hourNumber}} => 09
     *
     * @return The current clock 24-hour number.
     */
    @DefineSKFunction(name = "hourNumber", description = "Get the current clock 24-hour number")
    public String hourNumber() {
        return DateTimeFormatter.ofPattern("HH").format(ZonedDateTime.now());
    }

    /**
     * Get the date of offset from today by a provided number of days
     *
     * <p>Example: SKContext context = SKBuilders.context().build(); context.setVariable("input",
     * "3"); {{time.daysAgo $input}} => Saturday, January 11, 2031
     *
     * @param days Number of days to subtract from the current day
     * @return The date of offset from today by a provided number of days
     */
    @DefineSKFunction(
            name = "daysAgo",
            description = "Get the date of offset from today by a provided number of days")
    public static String daysAgo(String days) {
        int offsetDays = Integer.parseInt(days);
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR)
                .format(ZonedDateTime.now().minusDays(offsetDays));
    }

    /**
     * Get the date of the last day matching the supplied week day name
     *
     * <p>Example: {{time.dateMatchingLastDayName "Monday"}} => Monday, January 6, 2031
     *
     * @param dayName Name of the day to match
     * @return The date of the last day matching the supplied week day name
     */
    @DefineSKFunction(
            name = "dateMatchingLastDayName",
            description = "Get the date of the last day matching the supplied week day name")
    public static String dateMatchingLastDayName(String dayName) {
        ZonedDateTime currentDate = ZonedDateTime.now();
        Locale systemLocale = Locale.getDefault();
        for (int i = 1; i <= 7; i++) {
            currentDate = currentDate.minusDays(1);
            String currentDayName =
                    currentDate.getDayOfWeek().getDisplayName(TextStyle.FULL, systemLocale);

            if (currentDayName.equalsIgnoreCase(dayName)) {
                return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR).format(currentDate);
            }
        }
        throw new IllegalArgumentException("dayName is not recognized");
    }

    /**
     * Get the minutes on the current hour.
     *
     * <p>Example: {{time.minute}} => 15
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
     * <p>Example: {{time.second}} => 00
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
     * <p>Example: {{time.timeZoneOffset}} => +03:00
     *
     * @return The local time zone offset from UTC.
     */
    @DefineSKFunction(
            name = "timeZoneOffset",
            description = "Get the local time zone offset from UTC")
    public String timeZoneOffset() {
        return DateTimeFormatter.ofPattern("XXX").format(ZonedDateTime.now());
    }

    /**
     * Get the local time zone name.
     *
     * <p>Example: {{time.timeZoneName}} => Pacific Time
     *
     * @return The local time zone name.
     */
    @DefineSKFunction(name = "timeZoneName", description = "Get the local time zone name")
    public String timeZoneName() {
        ZoneId zoneId = ZoneId.systemDefault();
        return zoneId.getDisplayName(TextStyle.FULL, Locale.getDefault());
    }
}
