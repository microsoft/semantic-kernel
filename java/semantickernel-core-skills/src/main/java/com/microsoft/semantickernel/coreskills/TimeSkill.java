// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.util.LocaleParser;

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
     * Get the current date and time for the system default timezone.
     *
     * @return a ZonedDateTime object with the current date and time.
     */
    public ZonedDateTime now() {
        return ZonedDateTime.now(ZoneId.systemDefault());
    }

    /**
     * Get the current date.
     *
     * <p>Example: {{time.date}} => Sunday, January 12, 2025
     *
     * @return The current date.
     */
    @DefineSKFunction(name = "date", description = "Get the current date")
    public String date(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        // Example: Sunday, 12 January, 2025
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR)
                .withLocale(parseLocale(locale))
                .format(now());
    }

    /**
     * Get the current time.
     *
     * <p>Example: {{time.time}} => 9:15:00 AM
     *
     * @return The current time.
     */
    @DefineSKFunction(name = "time", description = "Get the current time")
    public String time(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        // Example: 09:15:07 PM
        return DateTimeFormatter.ofPattern("hh:mm:ss a")
                .withLocale(parseLocale(locale))
                .format(now());
    }

    /**
     * Get the current UTC date and time.
     *
     * <p>Example: {{time.utcNow}} => Sunday, January 13, 2025 5:15 AM
     *
     * @return The current UTC date and time.
     */
    @DefineSKFunction(name = "utcNow", description = "Get the current UTC date and time")
    public String utcNow(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR + " h:mm a")
                .withLocale(parseLocale(locale))
                .format(now().withZoneSameInstant(ZoneOffset.UTC));
    }

    /**
     * Get the current date (alias for date() method).
     *
     * <p>Example: {{time.today}} => Sunday, January 12, 2025
     *
     * @return The current date.
     */
    @DefineSKFunction(name = "today", description = "Get the current date")
    public String today(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return date(locale);
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
    public String now(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR + " h:mm a")
                .withLocale(parseLocale(locale))
                .format(now());
    }

    /**
     * Get the current year.
     *
     * <p>Example: {{time.year}} => 2025
     *
     * @return The current year.
     */
    @DefineSKFunction(name = "year", description = "Get the current year")
    public String year(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("yyyy").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the current month name.
     *
     * <p>Example: {{time.month}} => January
     *
     * @return The current month name.
     */
    @DefineSKFunction(name = "month", description = "Get the current month name")
    public String month(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("MMMM").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the current month number.
     *
     * <p>Example: {{time.monthNumber}} => 01
     *
     * @return The current month number.
     */
    @DefineSKFunction(name = "monthNumber", description = "Get the current month number")
    public String monthNumber(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("MM").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the current day of the month.
     *
     * <p>Example: {{time.day}} => 12
     *
     * @return The current day of the month.
     */
    @DefineSKFunction(name = "day", description = "Get the current day of the month")
    public String day(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("d").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the current day of the week.
     *
     * <p>Example: {{time.dayOfWeek}} => Sunday
     *
     * @return The current day of the week.
     */
    @DefineSKFunction(name = "dayOfWeek", description = "Get the current day of the week")
    public String dayOfWeek(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("EEEE").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the current clock hour.
     *
     * <p>Example: {{time.hour}} => 9 AM
     *
     * @return The current clock hour.
     */
    @DefineSKFunction(name = "hour", description = "Get the current clock hour")
    public String hour(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("h a").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the current clock 24-hour number.
     *
     * <p>Example: {{time.hourNumber}} => 09
     *
     * @return The current clock 24-hour number.
     */
    @DefineSKFunction(name = "hourNumber", description = "Get the current clock 24-hour number")
    public String hourNumber(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("HH").withLocale(parseLocale(locale)).format(now());
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
    public String daysAgo(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(
                            name = "input",
                            description = "Number of days to offset from today.")
                    String days,
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        int offsetDays = Integer.parseInt(days);
        return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR)
                .withLocale(parseLocale(locale))
                .format(now().minusDays(offsetDays));
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
    public String dateMatchingLastDayName(
            @SKFunctionInputAttribute
                    @SKFunctionParameters(name = "input", description = "Week name day.")
                    String dayName,
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        ZonedDateTime currentDate = now();
        for (int i = 1; i <= 7; i++) {
            currentDate = currentDate.minusDays(1);
            String currentDayName =
                    currentDate.getDayOfWeek().getDisplayName(TextStyle.FULL, parseLocale(locale));

            if (currentDayName.equalsIgnoreCase(dayName)) {
                return DateTimeFormatter.ofPattern(DAY_MONTH_DAY_YEAR)
                        .withLocale(parseLocale(locale))
                        .format(currentDate);
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
    public String minute(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("mm").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the seconds on the current minute.
     *
     * <p>Example: {{time.second}} => 00
     *
     * @return The seconds on the current minute.
     */
    @DefineSKFunction(name = "second", description = "Get the seconds on the current minute")
    public String second(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("ss").withLocale(parseLocale(locale)).format(now());
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
    public String timeZoneOffset(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        return DateTimeFormatter.ofPattern("XXX").withLocale(parseLocale(locale)).format(now());
    }

    /**
     * Get the local time zone name.
     *
     * <p>Example: {{time.timeZoneName}} => Pacific Time
     *
     * @return The local time zone name.
     */
    @DefineSKFunction(name = "timeZoneName", description = "Get the local time zone name")
    public String timeZoneName(
            @SKFunctionParameters(
                            name = "locale",
                            description = "Locale to use when formatting the date",
                            required = false)
                    String locale) {
        ZoneId zoneId = ZoneId.systemDefault();
        return zoneId.getDisplayName(TextStyle.FULL, parseLocale(locale));
    }

    /**
     * Parse the locale string into a Locale object.
     *
     * <p>By default, it parses using the LocaleParser utility class.
     *
     * @param locale string
     * @return a locale object
     */
    protected Locale parseLocale(String locale) {
        return LocaleParser.parseLocale(locale);
    }
}
