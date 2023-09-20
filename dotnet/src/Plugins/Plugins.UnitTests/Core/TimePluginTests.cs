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

// TODO: allow clock injection and test all functions
public class TimePluginTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var _ = new TimePlugin();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportPlugin(new TimePlugin(), "time");
    }

    [Fact]
    public void DaysAgo()
    {
        double interval = 2;
        DateTime expected = DateTime.Now.AddDays(-interval);
        var plugin = new TimePlugin();
        string result = plugin.DaysAgo(interval, CultureInfo.CurrentCulture);
        DateTime returned = DateTime.Parse(result, CultureInfo.CurrentCulture);
        Assert.Equal(expected.Day, returned.Day);
        Assert.Equal(expected.Month, returned.Month);
        Assert.Equal(expected.Year, returned.Year);
    }

    [Fact]
    public void Day()
    {
        string expected = DateTime.Now.ToString("dd", CultureInfo.CurrentCulture);
        var plugin = new TimePlugin();
        string result = plugin.Day(CultureInfo.CurrentCulture);
        Assert.Equal(expected, result);
        Assert.True(int.TryParse(result, out _));
    }

    [Fact]
    public async Task LastMatchingDayBadInputAsync()
    {
        var plugin = new TimePlugin();

        var ex = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => FunctionHelpers.CallViaKernelAsync(plugin, "DateMatchingLastDayName", ("input", "not a day name")));

        AssertExtensions.AssertIsArgumentOutOfRange(ex, "input", "not a day name");
    }

    [Theory]
    [MemberData(nameof(DayOfWeekEnumerator))]
    public void LastMatchingDay(DayOfWeek dayName)
    {
        int steps = 0;
        DateTime date = DateTime.Now.Date.AddDays(-1);
        while (date.DayOfWeek != dayName && steps <= 7)
        {
            date = date.AddDays(-1);
            steps++;
        }
        bool found = date.DayOfWeek == dayName;
        Assert.True(found);

        var plugin = new TimePlugin();
        string result = plugin.DateMatchingLastDayName(dayName, CultureInfo.CurrentCulture);
        DateTime returned = DateTime.Parse(result, CultureInfo.CurrentCulture);
        Assert.Equal(date.Day, returned.Day);
        Assert.Equal(date.Month, returned.Month);
        Assert.Equal(date.Year, returned.Year);
    }

    public static IEnumerable<object[]> DayOfWeekEnumerator()
    {
        foreach (var day in Enum.GetValues<DayOfWeek>())
        {
            yield return new object[] { day };
        }
    }
}
