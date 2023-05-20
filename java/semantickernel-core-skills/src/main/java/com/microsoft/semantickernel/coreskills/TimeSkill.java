// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills; // Copyright (c) Microsoft. All rights reserved.

import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;

import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;

public class TimeSkill {
    @DefineSKFunction(name = "date", description = "Get the current date")
    public String date() {
        // Example: Sunday, 12 January, 2025
        return DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(ZonedDateTime.now());
    }

    /*
        /// <summary>
        /// Get the current date
        /// </summary>
        /// <example>
        /// {{time.today}} => Sunday, 12 January, 2031
        /// </example>
        /// <returns> The current date </returns>
        [SKFunction("Get the current date")]
        public string Today() => this.Date();

        /// <summary>
        /// Get the current date and time in the local time zone"
        /// </summary>
        /// <example>
        /// {{time.now}} => Sunday, January 12, 2025 9:15 PM
        /// </example>
        /// <returns> The current date and time in the local time zone </returns>
        [SKFunction("Get the current date and time in the local time zone")]
        public string Now()
        {
            // Sunday, January 12, 2025 9:15 PM
            return DateTimeOffset.Now.ToString("f", CultureInfo.CurrentCulture);
        }

        /// <summary>
        /// Get the current UTC date and time
        /// </summary>
        /// <example>
        /// {{time.utcNow}} => Sunday, January 13, 2025 5:15 AM
        /// </example>
        /// <returns> The current UTC date and time </returns>
        [SKFunction("Get the current UTC date and time")]
        public string UtcNow()
        {
            // Sunday, January 13, 2025 5:15 AM
            return DateTimeOffset.UtcNow.ToString("f", CultureInfo.CurrentCulture);
        }
    */
    /// <summary>
    /// Get the current time
    /// </summary>
    /// <example>
    /// {{time.time}} => 09:15:07 PM
    /// </example>
    /// <returns> The current time </returns>
    @DefineSKFunction(name = "time", description = "Get the current time")
    public String time() {
        // Example: 09:15:07 PM
        return DateTimeFormatter.ofPattern("hh:mm:ss a").format(ZonedDateTime.now());
    }
    /*
       /// <summary>
       /// Get the current year
       /// </summary>
       /// <example>
       /// {{time.year}} => 2025
       /// </example>
       /// <returns> The current year </returns>
       [SKFunction("Get the current year")]
       public string Year()
       {
           // Example: 2025
           return DateTimeOffset.Now.ToString("yyyy", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the current month name
       /// </summary>
       /// <example>
       /// {time.month}} => January
       /// </example>
       /// <returns> The current month name </returns>
       [SKFunction("Get the current month name")]
       public string Month()
       {
           // Example: January
           return DateTimeOffset.Now.ToString("MMMM", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the current month number
       /// </summary>
       /// <example>
       /// {{time.monthNumber}} => 01
       /// </example>
       /// <returns> The current month number </returns>
       [SKFunction("Get the current month number")]
       public string MonthNumber()
       {
           // Example: 01
           return DateTimeOffset.Now.ToString("MM", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the current day of the month
       /// </summary>
       /// <example>
       /// {{time.day}} => 12
       /// </example>
       /// <returns> The current day of the month </returns>
       [SKFunction("Get the current day of the month")]
       public string Day()
       {
           // Example: 12
           return DateTimeOffset.Now.ToString("DD", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the current day of the week
       /// </summary>
       /// <example>
       /// {{time.dayOfWeek}} => Sunday
       /// </example>
       /// <returns> The current day of the week </returns>
       [SKFunction("Get the current day of the week")]
       public string DayOfWeek()
       {
           // Example: Sunday
           return DateTimeOffset.Now.ToString("dddd", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the current clock hour
       /// </summary>
       /// <example>
       /// {{time.hour}} => 9 PM
       /// </example>
       /// <returns> The current clock hour </returns>
       [SKFunction("Get the current clock hour")]
       public string Hour()
       {
           // Example: 9 PM
           return DateTimeOffset.Now.ToString("h tt", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the current clock 24-hour number
       /// </summary>
       /// <example>
       /// {{time.hourNumber}} => 21
       /// </example>
       /// <returns> The current clock 24-hour number </returns>
       [SKFunction("Get the current clock 24-hour number")]
       public string HourNumber()
       {
           // Example: 21
           return DateTimeOffset.Now.ToString("HH", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the minutes on the current hour
       /// </summary>
       /// <example>
       /// {{time.minute}} => 15
       /// </example>
       /// <returns> The minutes on the current hour </returns>
       [SKFunction("Get the minutes on the current hour")]
       public string Minute()
       {
           // Example: 15
           return DateTimeOffset.Now.ToString("mm", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the seconds on the current minute
       /// </summary>
       /// <example>
       /// {{time.second}} => 7
       /// </example>
       /// <returns> The seconds on the current minute </returns>
       [SKFunction("Get the seconds on the current minute")]
       public string Second()
       {
           // Example: 7
           return DateTimeOffset.Now.ToString("ss", CultureInfo.CurrentCulture);
       }

       /// <summary>
       /// Get the local time zone offset from UTC
       /// </summary>
       /// <example>
       /// {{time.timeZoneOffset}} => -08:00
       /// </example>
       /// <returns> The local time zone offset from UTC </returns>
       [SKFunction("Get the local time zone offset from UTC")]
       public string TimeZoneOffset()
       {
           // Example: -08:00
           return DateTimeOffset.Now.ToString("%K", CultureInfo.CurrentCulture);
       }

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
       [SKFunction("Get the local time zone name")]
       public string TimeZoneName()
       {
           // Example: PST
           // Note: this is the "current" timezone and it can change over the year, e.g. from PST to PDT
           return TimeZoneInfo.Local.DisplayName;
       }

    */
}
