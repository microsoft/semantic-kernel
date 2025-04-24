// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Runtime;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

public class OrchestrationResultTests
{
    [Fact]
    public void Constructor_InitializesPropertiesCorrectly()
    {
        // Arrange
        string orchestrationName = "TestOrchestration";
        TopicId topic = new("testTopic");
        TaskCompletionSource<string> tcs = new();

        // Act
        OrchestrationResult<string> result = new(orchestrationName, topic, tcs, NullLogger.Instance);

        // Assert
        Assert.Equal(topic, result.Topic);
    }

    [Fact]
    public async Task GetValueAsync_ReturnsCompletedValue_WhenTaskIsCompletedAsync()
    {
        // Arrange
        string orchestrationName = "TestOrchestration";
        TopicId topic = new("testTopic");
        TaskCompletionSource<string> tcs = new();
        OrchestrationResult<string> result = new(orchestrationName, topic, tcs, NullLogger.Instance);
        string expectedValue = "Result value";

        // Act
        tcs.SetResult(expectedValue);
        string actualValue = await result.GetValueAsync();

        // Assert
        Assert.Equal(expectedValue, actualValue);
    }

    [Fact]
    public async Task GetValueAsync_WithTimeout_ReturnsCompletedValue_WhenTaskCompletesWithinTimeoutAsync()
    {
        // Arrange
        string orchestrationName = "TestOrchestration";
        TopicId topic = new("testTopic");
        TaskCompletionSource<string> tcs = new();
        OrchestrationResult<string> result = new(orchestrationName, topic, tcs, NullLogger.Instance);
        string expectedValue = "Result value";
        TimeSpan timeout = TimeSpan.FromSeconds(1);

        // Act
        tcs.SetResult(expectedValue);
        string actualValue = await result.GetValueAsync(timeout);

        // Assert
        Assert.Equal(expectedValue, actualValue);
    }

    [Fact]
    public async Task GetValueAsync_WithTimeout_ThrowsTimeoutException_WhenTaskDoesNotCompleteWithinTimeoutAsync()
    {
        // Arrange
        string orchestrationName = "TestOrchestration";
        TopicId topic = new("testTopic");
        TaskCompletionSource<string> tcs = new();
        OrchestrationResult<string> result = new(orchestrationName, topic, tcs, NullLogger.Instance);
        TimeSpan timeout = TimeSpan.FromMilliseconds(50);

        // Act & Assert
        TimeoutException exception = await Assert.ThrowsAsync<TimeoutException>(() => result.GetValueAsync(timeout).AsTask());
        Assert.Contains("Orchestration did not complete within the allowed duration", exception.Message);
    }

    [Fact]
    public async Task GetValueAsync_ReturnsCompletedValue_WhenCompletionIsDelayedAsync()
    {
        // Arrange
        string orchestrationName = "TestOrchestration";
        TopicId topic = new("testTopic");
        TaskCompletionSource<int> tcs = new();
        OrchestrationResult<int> result = new(orchestrationName, topic, tcs, NullLogger.Instance);
        int expectedValue = 42;

        // Act
        // Simulate delayed completion in a separate task
        Task delayTask = Task.Run(async () =>
        {
            await Task.Delay(100);
            tcs.SetResult(expectedValue);
        });

        int actualValue = await result.GetValueAsync();

        // Assert
        Assert.Equal(expectedValue, actualValue);
    }
}
