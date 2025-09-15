// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

/// <summary>
/// Unit tests for activity extensions.
/// </summary>
public sealed class ActivityExtensionsTests
{
    [Fact]
    public async Task RunWithActivityByDefaultReturnsExpectedResultsAsync()
    {
        // Arrange
        var activityMock = new Mock<Activity>(MockBehavior.Loose, "ActivityName");

        // Act
        var results = await ActivityExtensions.RunWithActivityAsync(
            () => activityMock.Object,
            () => new[] { 1, 2, 3 }.ToAsyncEnumerable(), CancellationToken.None).ToListAsync();

        // Assert
        Assert.Equal(new[] { 1, 2, 3 }, results);
    }

    [Fact]
    public async Task RunWithActivityWhenOperationThrowsExceptionActivitySetsErrorAndThrowsAsync()
    {
        // Arrange
        var activityMock = new Mock<Activity>(MockBehavior.Loose, "ActivityName");

        // Act & Assert
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await ActivityExtensions.RunWithActivityAsync<int>(
                () => activityMock.Object,
                () => throw new InvalidOperationException("Test exception"),
                CancellationToken.None).ToListAsync());

        Assert.Equal("Test exception", ex.Message);
        Assert.Equal(ActivityStatusCode.Error, activityMock.Object.Status);

        var errorTag = activityMock.Object.Tags.FirstOrDefault(l => l.Key == "error.type");

        Assert.Contains(nameof(InvalidOperationException), errorTag.Value);
    }

    [Fact]
    public async Task RunWithActivityWhenEnumerationThrowsExceptionActivitySetsErrorAndThrows()
    {
        // Arrange
        var activityMock = new Mock<Activity>(MockBehavior.Loose, "ActivityName");

        async static IAsyncEnumerable<int> Operation()
        {
            yield return 1;
            await Task.Yield();
            throw new InvalidOperationException("Enumeration error");
        }

        // Act & Assert
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await ActivityExtensions.RunWithActivityAsync<int>(
                () => activityMock.Object,
                Operation,
                CancellationToken.None).ToListAsync());

        Assert.Equal("Enumeration error", ex.Message);
        Assert.Equal(ActivityStatusCode.Error, activityMock.Object.Status);

        var errorTag = activityMock.Object.Tags.FirstOrDefault(l => l.Key == "error.type");

        Assert.Contains(nameof(InvalidOperationException), errorTag.Value);
    }

    [Fact]
    public async Task RunWithActivityWhenCancellationRequestedThrowsTaskCanceledException()
    {
        // Arrange
        using var cts = new CancellationTokenSource();
        cts.Cancel();

        var activityMock = new Mock<Activity>(MockBehavior.Loose, "ActivityName");

        async static IAsyncEnumerable<int> Operation([EnumeratorCancellation] CancellationToken token)
        {
            await Task.Delay(10, token);
            yield return 1;
        }

        // Act & Assert
        var ex = await Assert.ThrowsAsync<TaskCanceledException>(async () =>
            await ActivityExtensions.RunWithActivityAsync<int>(
                () => activityMock.Object,
                () => Operation(cts.Token),
                cts.Token).ToListAsync());
    }
}
