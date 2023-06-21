// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;
import java.time.format.TextStyle;
import java.util.Locale;

/**
 * Description: TimeSkill provides a set of functions to get the current time
 * and date.
 *
 * Usage:
 * kernel.import_skill("time", TimeSkill())
 * Examples:
 * {{time.date}} => Sunday, 12 January, 2031
 * {{time.today}} => Sunday, 12 January, 2031
 * {{time.now}} => Sunday, January 12, 2031 9:15 PM
 * {{time.utcNow}} => Sunday, January 13, 2031 5:15 AM
 * {{time.time}} => 09:15:07 PM
 * {{time.year}} => 2031
 * {{time.month}} => January
 * {{time.monthNumber}} => 01
 * {{time.day}} => 12
 * {{time.dayOfWeek}} => Sunday
 * {{time.hour}} => 9 PM
 * {{time.hourNumber}} => 21
 * {{time.days_ago $days}} => Sunday, 7 May, 2023
 * {{time.last_matching_day $dayName}} => Sunday, 7 May, 2023
 * {{time.minute}} => 15
 * {{time.minutes}} => 15
 * {{time.second}} => 7
 * {{time.seconds}} => 7
 * {{time.timeZoneOffset}} => -0800
 * {{time.timeZoneName}} => PST
 *
 */

public class TimeSkill {

    /**
     * Get the current date.
     * Example:
     *   {{time.date}} => Sunday, 12 January, 2031
     *
     * @return The current date.
     */
    @DefineSKFunction(name = "date", description = "Get the current date")
    public String date() {
        return DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(ZonedDateTime.now());
    }

    /**
     * Get the current date.
     *
     * Example:
     *  {{time.today}} => Sunday, 12 January, 2031
     *
     * @return The current date.
     */
    @DefineSKFunction(name = "today", description = "Get the current date")
    public String today() {
        return DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(ZonedDateTime.now());
    }

    /**
     * Get the current date and time in the local time zone.
     *
     * Example:
     *  {{time.now}} => Sunday, January 12, 2031 9:15 PM
     *
     * @return The current date and time in the local time zone.
     */
    @DefineSKFunction(name = "now", description = "Get the current date and time in the local time zone")
    public String now() {
        return DateTimeFormatter.ofLocalizedDateTime(FormatStyle.FULL).format(ZonedDateTime.now());
    }

    /**
     * Get the current UTC date and time.
     *
     *  Example:
     *   {{time.utcNow}} => Sunday, January 13, 2031 5:15 AM
     *
     * @return The current UTC date and time.
     */
    @DefineSKFunction(name = "utcNow", description = "Get the current UTC date and time")
    public String utcNow() {
        return DateTimeFormatter.ofLocalizedDateTime(FormatStyle.FULL).format(ZonedDateTime.now(ZoneId.of("UTC")));
    }

    /**
     * Get the current time in the local time zone.
     *
     * Example:
     *  {{time.time}} => 09:15:07 PM
     *
     * @return The current time in the local time zone.
     */
    @DefineSKFunction(name = "time", description = "Get the current time")
    public String time() {
        return DateTimeFormatter.ofPattern("hh:mm:ss a").format(ZonedDateTime.now());
    }

    /**
     * Get the current year.
     *
     * Example:
     *  {{time.year}} => 2031
     *
     * @return The current year.
     */
    @DefineSKFunction(name = "year", description = "Get the current year")
    public String year() {
        int currentYear = LocalDate.now().getYear();
        return String.valueOf(currentYear);
    }

    /**
     * Get the current month.
     *
     * Example:
     *  {{time.month}} => January
     *
     * @return The current month.
     */
    @DefineSKFunction(name = "month", description = "Get the current month")
    public String month() {
        Locale systemLocale = Locale.getDefault();
        return LocalDate.now().getMonth().getDisplayName(TextStyle.FULL, systemLocale);
    }

    /**
     * Get the current month number.
     *
     * Example:
     *  {{time.monthNumber}} => 1
     *
     * @return
     */
    @DefineSKFunction(name = "monthNumber", description = "Get the current month number")
    public String monthNumber() {
        int monthNumber = LocalDate.now().getMonth().getValue();
        return String.valueOf(monthNumber);
    }

    /**
     * Get the current day.
     *
     * Example:
     *  {{time.day}} => 12
     *
     * @return
     */
    @DefineSKFunction(name = "day", description = "Get the current daye")
    public String day() {
        int day = LocalDate.now().getDayOfMonth();
        return String.valueOf(day);
    }

    /**
     * Get the current day of the week.
     *
     * Example:
     *  {{time.dayOfWeek}} => Sunday
     *
     * @return The current day of the week.
     */
    @DefineSKFunction(name = "dayOfWeek", description = "Get the current day of the week")
    public String dayOfWeek() {
        Locale systemLocale = Locale.getDefault();
        return LocalDate.now().getDayOfWeek().getDisplayName(TextStyle.FULL, systemLocale);
    }

    /**
     * Get the current hour.
     *
     * Example:
     *  {{time.hour}} => 9 PM
     *
     * @return
     */
    @DefineSKFunction(name = "hour", description = "Get the current hour")
    public String hour() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("h a");
        return LocalTime.now().format(formatter);
    }

    /**
     * Get the current hour number.
     *
     * Example:
     *  {{time.hourNumber}} => 21
     *
     * @return
     */
    @DefineSKFunction(name = "hourNumber", description = "Get the current hour number")
    public String hourNumber() {
        int hour = LocalTime.now().getHour();
        return String.valueOf(hour);
    }

    /**
     * Get the date of offset from today by a provided number of days
     *
     * Example:
     *   SKContext context = SKBuilders.context().build();
     *   context.setVariable("input", "3");
     *   {{time.daysAgo $input}} => Saturday, January 11, 2031
     *
     * @param days
     * @return The date of offset from today by a provided number of days
     */
    @DefineSKFunction(name = "daysAgo", description = "Get the date of offset from today by a provided number of days")
    public static String daysAgo(String days) {
        int offsetDays = Integer.parseInt(days);
        LocalDate currentDate = LocalDate.now();
        LocalDate offsetDate = currentDate.minusDays(offsetDays);
        return DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(offsetDate);
    }

    /**
     * Get the date of the last day matching the supplied week day name
     *
     * Example:
     *  {{time.dateMatchingLastDayName "Monday"}} => Monday, January 6, 2031
     *
     * @param dayName
     * @return The date of the last day matching the supplied week day name
     */
    @DefineSKFunction(name = "dateMatchingLastDayName", description = "Get the date of the last day matching the supplied week day name")
    public static String dateMatchingLastDayName(String dayName) {
        LocalDate currentDate = LocalDate.now();
        Locale systemLocale = Locale.getDefault();
        for (int i = 1; i <= 7; i++) {
            currentDate = currentDate.minusDays(1);
            String currentDayName = currentDate.getDayOfWeek().getDisplayName(TextStyle.FULL, systemLocale);

            if (currentDayName.equalsIgnoreCase(dayName)) {
                return DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(currentDate);
            }
        }
        throw new IllegalArgumentException("dayName is not recognized");
    }

    /**
     * Get the current minute
     *
     * Example:
     * {{time.minute}} => 15
     *
     * @return The current minute
     */
    @DefineSKFunction(name = "minute", description = "Get the current minute")
    public String minute() {
        int currentMinute = LocalTime.now().getMinute();
        return String.valueOf(currentMinute);
    }

    /**
     * Get the current second
     *
     * Example:
     *  {{time.second}} => 7
     *
     * @return The current second
     */
    @DefineSKFunction(name = "second", description = "Get the current time")
    public String second() {
        int currentSecond = LocalTime.now().getSecond();
        return String.valueOf(currentSecond);
    }

    /**
     * Get the current time zone offset
     *
     * Example:
     *  {{time.timeZoneOffset}} => -05:00
     *
     * @return The current time zone offset
     */
    @DefineSKFunction(name = "timeZoneOffset", description = "Get the current time")
    public String timeZoneOffset() {
        return ZonedDateTime.now().getOffset().toString();
    }

    /**
     * Get the current time zone name
     *
     * Example:
     * {{time.timeZoneName}} => Eastern Standard Time
     *
     * @return The current time zone name
     */
    @DefineSKFunction(name = "timeZoneName", description = "Get the current time")
    public String timeZoneName() {
        Locale systemLocale = Locale.getDefault();
        return ZonedDateTime.now().getZone().getDisplayName(TextStyle.FULL, systemLocale);
    }
}
