// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// TimePlugin provides a set of functions to get the current time and date.
/// </summary>
/// <remark>
/// Note: the time represents the time on the hw/vm/machine where the kernel is running.
/// TODO: import and use user's timezone
/// </remark>
public sealed class TimePlugin
{
    /// <summary>
    /// Get the current date
    /// </summary>
    /// <example>
    /// {{time.date}} => Sunday, 12 January, 2031
    /// </example>
    /// <returns> The current date </returns>
    [KernelFunction, Description("Get the current date")]
    public string Date(IFormatProvider? formatProvider = null) =>
        // Example: Sunday, 12 January, 2025
        DateTimeOffset.Now.ToString("D", formatProvider);

    /// <summary>
    /// Get the current date
    /// </summary>
    /// <example>
    /// {{time.today}} => Sunday, 12 January, 2031
    /// </example>
    /// <returns> The current date </returns>
    [KernelFunction, Description("Get the current date")]
    public string Today(IFormatProvider? formatProvider = null) =>
        // Example: Sunday, 12 January, 2025
        this.Date(formatProvider);

    /// <summary>
    /// Get the current date and time in the local time zone"
    /// </summary>
    /// <example>
    /// {{time.now}} => Sunday, January 12, 2025 9:15 PM
    /// </example>
    /// <returns> The current date and time in the local time zone </returns>
    [KernelFunction, Description("Get the current date and time in the local time zone")]
    public string Now(IFormatProvider? formatProvider = null) =>
        // Sunday, January 12, 2025 9:15 PM
        DateTimeOffset.Now.ToString("f", formatProvider);

    /// <summary>
    /// Get the current UTC date and time
    /// </summary>
    /// <example>
    /// {{time.utcNow}} => Sunday, January 13, 2025 5:15 AM
    /// </example>
    /// <returns> The current UTC date and time </returns>
    [KernelFunction, Description("Get the current UTC date and time")]
    public string UtcNow(IFormatProvider? formatProvider = null) =>
        // Sunday, January 13, 2025 5:15 AM
        DateTimeOffset.UtcNow.ToString("f", formatProvider);

    /// <summary>
    /// Get the current time
    /// </summary>
    /// <example>
    /// {{time.time}} => 09:15:07 PM
    /// </example>
    /// <returns> The current time </returns>
    [KernelFunction, Description("Get the current time")]
    public string Time(IFormatProvider? formatProvider = null) =>
        // Example: 09:15:07 PM
        DateTimeOffset.Now.ToString("hh:mm:ss tt", formatProvider);

    /// <summary>
    /// Get the current year
    /// </summary>
    /// <example>
    /// {{time.year}} => 2025
    /// </example>
    /// <returns> The current year </returns>
    [KernelFunction, Description("Get the current year")]
    public string Year(IFormatProvider? formatProvider = null) =>
        // Example: 2025
        DateTimeOffset.Now.ToString("yyyy", formatProvider);

    /// <summary>
    /// Get the current month name
    /// </summary>
    /// <example>
    /// {time.month}} => January
    /// </example>
    /// <returns> The current month name </returns>
    [KernelFunction, Description("Get the current month name")]
    public string Month(IFormatProvider? formatProvider = null) =>
        // Example: January
        DateTimeOffset.Now.ToString("MMMM", formatProvider);

    /// <summary>
    /// Get the current month number
    /// </summary>
    /// <example>
    /// {{time.monthNumber}} => 01
    /// </example>
    /// <returns> The current month number </returns>
    [KernelFunction, Description("Get the current month number")]
    public string MonthNumber(IFormatProvider? formatProvider = null) =>
        // Example: 01
        DateTimeOffset.Now.ToString("MM", formatProvider);

    /// <summary>
    /// Get the current day of the month
    /// </summary>
    /// <example>
    /// {{time.day}} => 12
    /// </example>
    /// <returns> The current day of the month </returns>
    [KernelFunction, Description("Get the current day of the month")]
    public string Day(IFormatProvider? formatProvider = null) =>
        // Example: 12
        DateTimeOffset.Now.ToString("dd", formatProvider);

    /// <summary>
    /// Get the date a provided number of days in the past
    /// </summary>
    /// <returns> The date the provided number of days before today </returns>
    [KernelFunction]
    [Description("Get the date offset by a provided number of days from today")]
    public string DaysAgo([Description("The number of days to offset from today")] double input, IFormatProvider? formatProvider = null) =>
        DateTimeOffset.Now.AddDays(-input).ToString("D", formatProvider);

    /// <summary>
    /// Get the current day of the week
    /// </summary>
    /// <example>
    /// {{time.dayOfWeek}} => Sunday
    /// </example>
    /// <returns> The current day of the week </returns>
    [KernelFunction, Description("Get the current day of the week")]
    public string DayOfWeek(IFormatProvider? formatProvider = null) =>
        // Example: Sunday
        DateTimeOffset.Now.ToString("dddd", formatProvider);

    /// <summary>
    /// Get the current clock hour
    /// </summary>
    /// <example>
    /// {{time.hour}} => 9 PM
    /// </example>
    /// <returns> The current clock hour </returns>
    [KernelFunction, Description("Get the current clock hour")]
    public string Hour(IFormatProvider? formatProvider = null) =>
        // Example: 9 PM
        DateTimeOffset.Now.ToString("h tt", formatProvider);

    /// <summary>
    /// Get the current clock 24-hour number
    /// </summary>
    /// <example>
    /// {{time.hourNumber}} => 21
    /// </example>
    /// <returns> The current clock 24-hour number </returns>
    [KernelFunction, Description("Get the current clock 24-hour number")]
    public string HourNumber(IFormatProvider? formatProvider = null) =>
        // Example: 21
        DateTimeOffset.Now.ToString("HH", formatProvider);

    /// <summary>
    /// Get the date of the previous day matching the supplied day name
    /// </summary>
    /// <example>
    /// {{time.lastMatchingDay $dayName}} => Sunday, 7 May, 2023
    /// </example>
    /// <returns> The date of the last instance of this day name </returns>
    /// <exception cref="ArgumentOutOfRangeException">dayName is not a recognized name of a day of the week</exception>
    [KernelFunction]
    [Description("Get the date of the last day matching the supplied week day name in English. Example: Che giorno era 'Martedi' scorso -> dateMatchingLastDayName 'Tuesday' => Tuesday, 16 May, 2023")]
    public string DateMatchingLastDayName(
        [Description("The day name to match")] DayOfWeek input,
        IFormatProvider? formatProvider = null)
    {
        DateTimeOffset dateTime = DateTimeOffset.Now;

        // Walk backwards from the previous day for up to a week to find the matching day
        for (int i = 1; i <= 7; ++i)
        {
            dateTime = dateTime.AddDays(-1);
            if (dateTime.DayOfWeek == input)
            {
                break;
            }
        }

        return dateTime.ToString("D", formatProvider);
    }

    /// <summary>
    /// Get the minutes on the current hour
    /// </summary>
    /// <example>
    /// {{time.minute}} => 15
    /// </example>
    /// <returns> The minutes on the current hour </returns>
    [KernelFunction, Description("Get the minutes on the current hour")]
    public string Minute(IFormatProvider? formatProvider = null) =>
        // Example: 15
        DateTimeOffset.Now.ToString("mm", formatProvider);

    /// <summary>
    /// Get the seconds on the current minute
    /// </summary>
    /// <example>
    /// {{time.second}} => 7
    /// </example>
    /// <returns> The seconds on the current minute </returns>
    [KernelFunction, Description("Get the seconds on the current minute")]
    public string Second(IFormatProvider? formatProvider = null) =>
        // Example: 07
        DateTimeOffset.Now.ToString("ss", formatProvider);

    /// <summary>
    /// Get the local time zone offset from UTC
    /// </summary>
    /// <example>
    /// {{time.timeZoneOffset}} => -08:00
    /// </example>
    /// <returns> The local time zone offset from UTC </returns>
    [KernelFunction, Description("Get the local time zone offset from UTC")]
    public string TimeZoneOffset(IFormatProvider? formatProvider = null) =>
        // Example: -08:00
        DateTimeOffset.Now.ToString("%K", formatProvider);

    /// <summary>
    /// Get the local time zone name
    /// </summary>
    /// <example>
    /// {{time.timeZoneName}} => PST
    /// </example>
    /// <remark>
    /// Note: this is the "current" timezone and it can change over the year, e.g. from PST to PDT
    /// </remark>
    /// <returns> The local time zone name </returns>
    [KernelFunction, Description("Get the local time zone name")]
    public string TimeZoneName() =>
        // Example: PST
        // Note: this is the "current" timezone and it can change over the year, e.g. from PST to PDT
        TimeZoneInfo.Local.DisplayName;
}
