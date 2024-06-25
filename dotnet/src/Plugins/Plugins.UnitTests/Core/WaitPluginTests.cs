// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Time.Testing;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using SemanticKernel.UnitTests;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

// TODO: allow clock injection and test all functions
public class WaitPluginTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var _ = new WaitPlugin();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Act - Assert no exception occurs e.g. due to reflection
        Assert.NotNull(KernelPluginFactory.CreateFromType<WaitPlugin>("wait"));
    }

    [Theory]
    [InlineData("0", 0)]
    [InlineData("100", 100000)]
    [InlineData("20.1", 20100)]
    [InlineData("0.1", 100)]
    [InlineData("0.01", 10)]
    [InlineData("0.001", 1)]
    [InlineData("0.0001", 0)]
    [InlineData("-0.0001", 0)]
    [InlineData("-10000", 0)]
    public async Task ItWaitSecondsWhenValidParametersSucceedAsync(string textSeconds, int expectedMilliseconds)
    {
        // Arrange
        var timeProvider = new FakeTimeProvider();
        var target = new WaitPlugin(timeProvider);
        var expectedTimeSpan = TimeSpan.FromMilliseconds(expectedMilliseconds);

        // Act and Assert
        long startingTime = timeProvider.GetTimestamp();
        Task wait = KernelPluginFactory.CreateFromObject(target)["Seconds"].InvokeAsync(new(), new() { ["seconds"] = textSeconds });

        if (expectedMilliseconds > 0)
        {
            timeProvider.Advance(TimeSpan.FromMilliseconds(expectedMilliseconds - 1));
            Assert.False(wait.IsCompleted);
        }

        timeProvider.Advance(TimeSpan.FromMilliseconds(1));
        await wait;

        Assert.InRange(timeProvider.GetElapsedTime(startingTime).TotalMilliseconds, expectedMilliseconds, double.MaxValue);
    }

    [Theory]
    [InlineData("$0")]
    [InlineData("one hundred")]
    [InlineData("20..,,2,1")]
    [InlineData(".2,2.1")]
    [InlineData("0.1.0")]
    [InlineData("00-099")]
    [InlineData("¹²¹")]
    [InlineData("2²")]
    [InlineData("zero")]
    [InlineData("-100 seconds")]
    [InlineData("1 second")]
    public async Task ItWaitSecondsWhenInvalidParametersFailsAsync(string textSeconds)
    {
        // Arrange
        KernelFunction func = KernelPluginFactory.CreateFromType<WaitPlugin>()["Seconds"];

        // Act
        var ex = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => func.InvokeAsync(new(), new() { ["seconds"] = textSeconds }));

        // Assert
        AssertExtensions.AssertIsArgumentOutOfRange(ex, "seconds", textSeconds);
    }
}
