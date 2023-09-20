// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using Moq;
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
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportSkill(new WaitPlugin(), "wait");
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
        var waitProviderMock = new Mock<WaitPlugin.IWaitProvider>();
        var target = new WaitPlugin(waitProviderMock.Object);

        // Act
        var context = await FunctionHelpers.CallViaKernelAsync(target, "Seconds", ("input", textSeconds));

        // Assert
        waitProviderMock.Verify(w => w.DelayAsync(It.IsIn(expectedMilliseconds)), Times.Once);
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
        var waitProviderMock = new Mock<WaitPlugin.IWaitProvider>();
        var target = new WaitPlugin(waitProviderMock.Object);

        // Act
        var ex = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => FunctionHelpers.CallViaKernelAsync(target, "Seconds", ("input", textSeconds)));

        // Assert
        AssertExtensions.AssertIsArgumentOutOfRange(ex, "seconds", textSeconds);
    }
}
