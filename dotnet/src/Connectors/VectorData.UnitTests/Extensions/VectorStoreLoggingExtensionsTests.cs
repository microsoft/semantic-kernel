// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreLoggingExtensionsTests
{
    [Fact]
    public async Task RunWithLoggingVoidLogsSuccess()
    {
        // Arrange
        var logger = new FakeLogger();
        static Task Operation() => Task.CompletedTask;

        // Act
        await VectorStoreLoggingExtensions.RunWithLoggingAsync(logger, "TestOperation", Operation);

        // Assert
        var logs = logger.Logs;
        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Debug, logs[1].Level);
        Assert.Equal("TestOperation completed.", logs[1].Message);
        Assert.Null(logs[1].Exception);
    }

    [Fact]
    public async Task RunWithLoggingVoidLogsException()
    {
        // Arrange
        var logger = new FakeLogger();
        static Task Operation() => throw new InvalidOperationException("Test error");

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            VectorStoreLoggingExtensions.RunWithLoggingAsync(logger, "TestOperation", Operation));

        Assert.Equal("Test error", exception.Message);

        var logs = logger.Logs;
        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Error, logs[1].Level);
        Assert.Equal("TestOperation failed.", logs[1].Message);
        Assert.Equal("Test error", logs[1].Exception?.Message);
    }

    [Fact]
    public async Task RunWithLoggingVoidLogsCancellation()
    {
        // Arrange
        var logger = new FakeLogger();
        using var cts = new CancellationTokenSource();
        Task Operation() => Task.FromCanceled(cts.Token);
        cts.Cancel();

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() =>
            VectorStoreLoggingExtensions.RunWithLoggingAsync(logger, "TestOperation", Operation));

        var logs = logger.Logs;
        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Debug, logs[1].Level);
        Assert.Equal("TestOperation canceled.", logs[1].Message);
        Assert.Null(logs[1].Exception);
    }

    [Fact]
    public async Task RunWithLoggingWithResultReturnsValue()
    {
        // Arrange
        var logger = new FakeLogger();
        static Task<int> Operation() => Task.FromResult(42);

        // Act
        var result = await VectorStoreLoggingExtensions.RunWithLoggingAsync(logger, "TestOperation", Operation);

        // Assert
        Assert.Equal(42, result);

        var logs = logger.Logs;

        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Debug, logs[1].Level);
        Assert.Equal("TestOperation completed.", logs[1].Message);
        Assert.Null(logs[1].Exception);
    }

    [Fact]
    public async Task RunWithLoggingWithResultLogsException()
    {
        // Arrange
        var logger = new FakeLogger();
        static Task<int> Operation() => throw new InvalidOperationException("Test error");

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            VectorStoreLoggingExtensions.RunWithLoggingAsync(logger, "TestOperation", Operation));

        Assert.Equal("Test error", exception.Message);

        var logs = logger.Logs;
        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Error, logs[1].Level);
        Assert.Equal("TestOperation failed.", logs[1].Message);
        Assert.Equal("Test error", logs[1].Exception?.Message);
    }

    [Fact]
    public async Task RunWithLoggingEnumerableYieldsValues()
    {
        // Arrange
        var logger = new FakeLogger();
        static async IAsyncEnumerable<int> Operation()
        {
            yield return 1;
            yield return 2;
            await Task.CompletedTask; // Ensure async behavior
        }

        // Act
        var results = new List<int>();
        await foreach (var item in VectorStoreLoggingExtensions.RunWithLoggingAsync(logger, "TestOperation", Operation, default))
        {
            results.Add(item);
        }

        // Assert
        Assert.Equal(new[] { 1, 2 }, results);

        var logs = logger.Logs;

        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Debug, logs[1].Level);
        Assert.Equal("TestOperation completed.", logs[1].Message);
        Assert.Null(logs[1].Exception);
    }

    [Fact]
    public async Task RunWithLoggingEnumerableLogsException()
    {
        // Arrange
        var logger = new FakeLogger();
        static async IAsyncEnumerable<int> Operation()
        {
            yield return 1;
            await Task.CompletedTask;
            throw new InvalidOperationException("Test error");
        }

        // Act & Assert
        var results = new List<int>();
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(async () =>
        {
            await foreach (var item in VectorStoreLoggingExtensions.RunWithLoggingAsync(logger, "TestOperation", Operation, default))
            {
                results.Add(item);
            }
        });

        Assert.Equal("Test error", exception.Message);
        Assert.Equal(new[] { 1 }, results);

        var logs = logger.Logs;

        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Error, logs[1].Level);
        Assert.Equal("TestOperation failed.", logs[1].Message);
        Assert.Equal("Test error", logs[1].Exception?.Message);
    }

    [Fact]
    public async Task RunWithLoggingEnumerableLogsCancellation()
    {
        // Arrange
        var logger = new FakeLogger();
        using var cts = new CancellationTokenSource();
        static async IAsyncEnumerable<int> Operation([EnumeratorCancellation] CancellationToken token)
        {
            yield return 1;
            await Task.Delay(10, token); // Simulate async work
            yield return 2;
        }
        cts.Cancel();

        // Act & Assert
        var results = new List<int>();
        var exception = await Assert.ThrowsAsync<TaskCanceledException>(async () =>
        {
            await foreach (var item in VectorStoreLoggingExtensions.RunWithLoggingAsync(
                logger,
                "TestOperation",
                () => Operation(cts.Token),
                cts.Token))
            {
                results.Add(item);
            }
        });

        Assert.Equal(new[] { 1 }, results); // Should yield first value before cancellation

        var logs = logger.Logs;

        Assert.Equal(2, logs.Count);
        Assert.Equal(LogLevel.Debug, logs[0].Level);
        Assert.Equal("TestOperation invoked.", logs[0].Message);
        Assert.Null(logs[0].Exception);
        Assert.Equal(LogLevel.Debug, logs[1].Level);
        Assert.Equal("TestOperation canceled.", logs[1].Message);
        Assert.Null(logs[1].Exception);
    }

    #region private

#pragma warning disable CA1812
    private sealed class TestRecord
    {
        [VectorStoreRecordData]
        public string DataProperty { get; set; } = "test value";

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> VectorProperty { get; set; } = new float[] { 1.0f, 2.0f, 3.0f };
    }
#pragma warning restore CA1812
    #endregion
}
