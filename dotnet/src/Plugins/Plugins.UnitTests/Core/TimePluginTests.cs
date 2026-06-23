// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

public class TimePluginTests
{
    // Sunday, 15 June 2025 21:15:07 UTC — local timezone pinned to UTC so tests are machine-independent
    private static readonly DateTimeOffset s_fixedTime = new(2025, 6, 15, 21, 15, 7, TimeSpan.Zero);

    private static TimePlugin CreatePlugin() => new(new FixedUtcTimeProvider(s_fixedTime));

    /// <summary>Minimal TimeProvider that returns a fixed UTC instant with UTC as local timezone.</summary>
    private sealed class FixedUtcTimeProvider(DateTimeOffset fixedUtc) : TimeProvider
    {
        public override DateTimeOffset GetUtcNow() => fixedUtc.ToUniversalTime();
        public override TimeZoneInfo LocalTimeZone => TimeZoneInfo.Utc;
    }

    [Fact]
    public void ItCanBeInstantiated()
    {
        var _ = new TimePlugin();
    }

    [Fact]
    public void ItCanBeImported()
    {
        Assert.NotNull(KernelPluginFactory.CreateFromType<TimePlugin>("time"));
    }

    [Fact]
    public void Date()
    {
        // InvariantCulture "D" format: dddd, dd MMMM yyyy
        Assert.Equal("Sunday, 15 June 2025", CreatePlugin().Date(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Today()
    {
        Assert.Equal("Sunday, 15 June 2025", CreatePlugin().Today(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Now()
    {
        // InvariantCulture "f" format: dddd, dd MMMM yyyy HH:mm
        Assert.Equal("Sunday, 15 June 2025 21:15", CreatePlugin().Now(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void UtcNow()
    {
        Assert.Equal("Sunday, 15 June 2025 21:15", CreatePlugin().UtcNow(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Time()
    {
        Assert.Equal("09:15:07 PM", CreatePlugin().Time(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Year()
    {
        Assert.Equal("2025", CreatePlugin().Year(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Month()
    {
        Assert.Equal("June", CreatePlugin().Month(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void MonthNumber()
    {
        Assert.Equal("06", CreatePlugin().MonthNumber(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Day()
    {
        Assert.Equal("15", CreatePlugin().Day(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void DayOfWeek()
    {
        Assert.Equal("Sunday", CreatePlugin().DayOfWeek(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Hour()
    {
        Assert.Equal("9 PM", CreatePlugin().Hour(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void HourNumber()
    {
        Assert.Equal("21", CreatePlugin().HourNumber(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Minute()
    {
        Assert.Equal("15", CreatePlugin().Minute(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Second()
    {
        Assert.Equal("07", CreatePlugin().Second(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void TimeZoneOffset()
    {
        Assert.Equal("+00:00", CreatePlugin().TimeZoneOffset(CultureInfo.InvariantCulture));
    }

    [Fact]
    public void TimeZoneName()
    {
        // FixedUtcTimeProvider pins LocalTimeZone to TimeZoneInfo.Utc
        Assert.Equal(TimeZoneInfo.Utc.DisplayName, CreatePlugin().TimeZoneName());
    }

    [Fact]
    public void DaysAgo()
    {
        // 2 days before 2025-06-15 is 2025-06-13 (Friday)
        Assert.Equal("Friday, 13 June 2025", CreatePlugin().DaysAgo(2, CultureInfo.InvariantCulture));
    }

    [Theory]
    [MemberData(nameof(DayOfWeekCases))]
    public void DateMatchingLastDayName(DayOfWeek dayName, string expectedDate)
    {
        // Fixed time is Sunday 2025-06-15; walk back to find each day
        Assert.Equal(expectedDate, CreatePlugin().DateMatchingLastDayName(dayName, CultureInfo.InvariantCulture));
    }

    public static IEnumerable<object[]> DayOfWeekCases()
    {
        // From Sunday 2025-06-15, the previous occurrence of each day (never same day).
        // InvariantCulture "D" format: dddd, dd MMMM yyyy
        yield return [System.DayOfWeek.Saturday, "Saturday, 14 June 2025"];
        yield return [System.DayOfWeek.Friday, "Friday, 13 June 2025"];
        yield return [System.DayOfWeek.Thursday, "Thursday, 12 June 2025"];
        yield return [System.DayOfWeek.Wednesday, "Wednesday, 11 June 2025"];
        yield return [System.DayOfWeek.Tuesday, "Tuesday, 10 June 2025"];
        yield return [System.DayOfWeek.Monday, "Monday, 09 June 2025"];
        yield return [System.DayOfWeek.Sunday, "Sunday, 08 June 2025"];
    }

    [Fact]
    public async Task LastMatchingDayBadInputAsync()
    {
        KernelFunction func = KernelPluginFactory.CreateFromType<TimePlugin>()["DateMatchingLastDayName"];

        var ex = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => func.InvokeAsync(new(), new() { ["input"] = "not a day name" }));

        AssertExtensions.AssertIsArgumentOutOfRange(ex, "input", "not a day name");
    }
}
