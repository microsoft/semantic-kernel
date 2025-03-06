// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI;

/// <summary>
/// Unit testing of <see cref="RunPollingOptions"/>.
/// </summary>
public class RunPollingOptionsTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void RunPollingOptionsInitialStateTest()
    {
        // Arrange
        RunPollingOptions options = new();

        // Assert
        Assert.Equal(RunPollingOptions.DefaultPollingInterval, options.RunPollingInterval);
        Assert.Equal(RunPollingOptions.DefaultPollingBackoff, options.RunPollingBackoff);
        Assert.Equal(RunPollingOptions.DefaultMessageSynchronizationDelay, options.MessageSynchronizationDelay);
        Assert.Equal(RunPollingOptions.DefaultPollingBackoffThreshold, options.RunPollingBackoffThreshold);
    }

    /// <summary>s
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void RunPollingOptionsAssignmentTest()
    {
        // Arrange
        RunPollingOptions options =
            new()
            {
                RunPollingInterval = TimeSpan.FromSeconds(3),
                RunPollingBackoff = TimeSpan.FromSeconds(4),
                RunPollingBackoffThreshold = 8,
                MessageSynchronizationDelay = TimeSpan.FromSeconds(5),
            };

        // Assert
        Assert.Equal(3, options.RunPollingInterval.TotalSeconds);
        Assert.Equal(4, options.RunPollingBackoff.TotalSeconds);
        Assert.Equal(5, options.MessageSynchronizationDelay.TotalSeconds);
        Assert.Equal(8, options.RunPollingBackoffThreshold);
    }

    /// <summary>s
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void RunPollingOptionsGetIntervalTest()
    {
        // Arrange
        RunPollingOptions options =
            new()
            {
                RunPollingInterval = TimeSpan.FromSeconds(3),
                RunPollingBackoff = TimeSpan.FromSeconds(4),
                RunPollingBackoffThreshold = 8,
            };

        // Assert
        Assert.Equal(options.RunPollingInterval, options.GetPollingInterval(8));
        Assert.Equal(options.RunPollingBackoff, options.GetPollingInterval(9));
    }
}
