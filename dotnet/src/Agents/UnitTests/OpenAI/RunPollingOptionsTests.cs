// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

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
        RunPollingOptions options = new();

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
        RunPollingOptions options =
            new()
            {
                RunPollingInterval = TimeSpan.FromSeconds(3),
                RunPollingBackoff = TimeSpan.FromSeconds(4),
                RunPollingBackoffThreshold = 8,
                MessageSynchronizationDelay = TimeSpan.FromSeconds(5),
            };

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
        RunPollingOptions options =
            new()
            {
                RunPollingInterval = TimeSpan.FromSeconds(3),
                RunPollingBackoff = TimeSpan.FromSeconds(4),
                RunPollingBackoffThreshold = 8,
            };

        Assert.Equal(options.RunPollingInterval, options.GetPollingInterval(8));
        Assert.Equal(options.RunPollingBackoff, options.GetPollingInterval(9));
    }
}
