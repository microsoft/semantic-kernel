// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingVectorStoreRecordCollectionTests : BaseLoggingTests
{
    [Fact]
    public void ConstructorThrowsOnNullInnerCollection()
    {
        // Arrange
        var logger = new Mock<ILogger>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorStoreRecordCollection<string, string>(null!, logger));
    }

    [Fact]
    public void ConstructorThrowsOnNullLogger()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorStoreRecordCollection<string, string>(innerCollection, null!));
    }

    [Fact]
    public void CollectionNameReturnsInnerCollectionName()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var logger = new Mock<ILogger>().Object;
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        var result = collection.CollectionName;

        // Assert
        Assert.Equal("testCollection", result);
    }

    [Fact]
    public async Task CollectionExistsDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.CollectionExistsAsync(default)).ReturnsAsync(true);
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        var result = await collection.CollectionExistsAsync();

        // Assert
        Assert.True(result);
        innerCollection.Verify(c => c.CollectionExistsAsync(default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "CollectionExistsAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "CollectionExistsAsync completed. Collection name: testCollection. Collection exists: True");
    }

    [Fact]
    public async Task CollectionExistsLogsCancellationAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.CollectionExistsAsync(cts.Token))
                       .Returns(Task.FromCanceled<bool>(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.CollectionExistsAsync(cts.Token));
        innerCollection.Verify(c => c.CollectionExistsAsync(cts.Token), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "CollectionExistsAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "CollectionExistsAsync canceled. Collection name: testCollection.");
    }

    [Fact]
    public async Task CollectionExistsLogsExceptionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.CollectionExistsAsync(default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.CollectionExistsAsync());

        innerCollection.Verify(c => c.CollectionExistsAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "CollectionExistsAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Error, "CollectionExistsAsync failed. CollectionName: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Fact]
    public async Task CreateCollectionDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.CreateCollectionAsync(default)).Returns(Task.CompletedTask);
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        await collection.CreateCollectionAsync();

        // Assert
        innerCollection.Verify(c => c.CreateCollectionAsync(default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionAsync completed. Collection name: testCollection.");
    }

    [Fact]
    public async Task CreateCollectionLogsCancellationAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.CreateCollectionAsync(cts.Token))
                       .Returns(Task.FromCanceled(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.CreateCollectionAsync(cts.Token));
        innerCollection.Verify(c => c.CreateCollectionAsync(cts.Token), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionAsync canceled. Collection name: testCollection.");
    }

    [Fact]
    public async Task CreateCollectionLogsExceptionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.CreateCollectionAsync(default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.CreateCollectionAsync());
        innerCollection.Verify(c => c.CreateCollectionAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Error, "CreateCollectionAsync failed. CollectionName: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.CreateCollectionIfNotExistsAsync(default)).Returns(Task.CompletedTask);
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        await collection.CreateCollectionIfNotExistsAsync();

        // Assert
        innerCollection.Verify(c => c.CreateCollectionIfNotExistsAsync(default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionIfNotExistsAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionIfNotExistsAsync completed. Collection name: testCollection.");
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsLogsCancellationAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.CreateCollectionIfNotExistsAsync(cts.Token))
                       .Returns(Task.FromCanceled(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.CreateCollectionIfNotExistsAsync(cts.Token));
        innerCollection.Verify(c => c.CreateCollectionIfNotExistsAsync(cts.Token), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionIfNotExistsAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionIfNotExistsAsync canceled. Collection name: testCollection.");
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsLogsExceptionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.CreateCollectionIfNotExistsAsync(default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.CreateCollectionIfNotExistsAsync());

        innerCollection.Verify(c => c.CreateCollectionIfNotExistsAsync(default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionIfNotExistsAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Error, "CreateCollectionIfNotExistsAsync failed. CollectionName: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task DeleteDelegatesToInnerCollectionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.DeleteAsync("key1", default)).Returns(Task.CompletedTask);

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        await collection.DeleteAsync("key1");

        // Assert
        innerCollection.Verify(c => c.DeleteAsync("key1", default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteAsync invoked. Collection Name: testCollection. Key: key1.");
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteAsync completed. Collection Name: testCollection. Key: key1.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteAsync invoked. Collection Name: testCollection.");
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteAsync completed. Collection Name: testCollection.");
        }
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task DeleteLogsCancellationAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.DeleteAsync("key1", cts.Token))
                       .Returns(Task.FromCanceled(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.DeleteAsync("key1", cts.Token));

        innerCollection.Verify(c => c.DeleteAsync("key1", cts.Token), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteAsync invoked. Collection Name: testCollection. Key: key1.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Debug, "DeleteAsync canceled. Collection Name: testCollection.");
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task DeleteLogsExceptionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.DeleteAsync("key1", default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.DeleteAsync("key1"));
        innerCollection.Verify(c => c.DeleteAsync("key1", default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteAsync invoked. Collection Name: testCollection. Key: key1.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Error, "DeleteAsync failed. Collection Name: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task DeleteBatchDelegatesToInnerCollectionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var keys = new[] { "key1", "key2" };
        innerCollection.Setup(c => c.DeleteBatchAsync(keys, default)).Returns(Task.CompletedTask);

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        await collection.DeleteBatchAsync(keys);

        // Assert
        innerCollection.Verify(c => c.DeleteBatchAsync(keys, default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteBatchAsync invoked. Collection Name: testCollection. Keys: key1,key2.");
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteBatchAsync completed. Collection Name: testCollection. Keys: key1,key2.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteBatchAsync invoked. Collection Name: testCollection.");
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteBatchAsync completed. Collection Name: testCollection.");
        }
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task DeleteBatchLogsCancellationAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var keys = new[] { "key1", "key2" };
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.DeleteBatchAsync(keys, cts.Token))
                       .Returns(Task.FromCanceled(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.DeleteBatchAsync(keys, cts.Token));
        innerCollection.Verify(c => c.DeleteBatchAsync(keys, cts.Token), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteBatchAsync invoked. Collection Name: testCollection. Keys: key1,key2.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteBatchAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Debug, "DeleteBatchAsync canceled. Collection Name: testCollection.");
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task DeleteBatchLogsExceptionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var keys = new[] { "key1", "key2" };
        innerCollection.Setup(c => c.DeleteBatchAsync(keys, default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.DeleteBatchAsync(keys));
        innerCollection.Verify(c => c.DeleteBatchAsync(keys, default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "DeleteBatchAsync invoked. Collection Name: testCollection. Keys: key1,key2.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "DeleteBatchAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Error, "DeleteBatchAsync failed. Collection Name: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Fact]
    public async Task DeleteCollectionDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.DeleteCollectionAsync(default)).Returns(Task.CompletedTask);
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        await collection.DeleteCollectionAsync();

        // Assert
        innerCollection.Verify(c => c.DeleteCollectionAsync(default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteCollectionAsync invoked. Collection Name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteCollectionAsync completed. CollectionName: testCollection.");
    }

    [Fact]
    public async Task DeleteCollectionLogsCancellationAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.DeleteCollectionAsync(cts.Token))
                       .Returns(Task.FromCanceled(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.DeleteCollectionAsync(cts.Token));
        innerCollection.Verify(c => c.DeleteCollectionAsync(cts.Token), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteCollectionAsync invoked. Collection Name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteCollectionAsync canceled. CollectionName: testCollection.");
    }

    [Fact]
    public async Task DeleteCollectionLogsExceptionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.DeleteCollectionAsync(default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.DeleteCollectionAsync());
        innerCollection.Verify(c => c.DeleteCollectionAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "DeleteCollectionAsync invoked. Collection Name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Error, "DeleteCollectionAsync failed. CollectionName: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task GetDelegatesToInnerCollectionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.GetAsync("key1", null, default)).ReturnsAsync("record1");
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        var result = await collection.GetAsync("key1");

        // Assert
        Assert.Equal("record1", result);
        innerCollection.Verify(c => c.GetAsync("key1", null, default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "GetAsync invoked. Collection Name: testCollection. Key: key1.");
            AssertLog(logger.Logs, LogLevel.Trace, "GetAsync completed. Collection Name: testCollection. Key: key1.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "GetAsync invoked. Collection Name: testCollection.");
            AssertLog(logger.Logs, LogLevel.Debug, "GetAsync completed. Collection Name: testCollection.");
        }
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task GetLogsCancellationAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.GetAsync("key1", null, cts.Token))
                       .Returns(Task.FromCanceled<string?>(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.GetAsync("key1", null, cts.Token));
        innerCollection.Verify(c => c.GetAsync("key1", null, cts.Token), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "GetAsync invoked. Collection Name: testCollection. Key: key1.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "GetAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Debug, "GetAsync canceled. Collection Name: testCollection.");
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task GetLogsExceptionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.GetAsync("key1", null, default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.GetAsync("key1"));
        innerCollection.Verify(c => c.GetAsync("key1", null, default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "GetAsync invoked. Collection Name: testCollection. Key: key1.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "GetAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Error, "GetAsync failed. Collection Name: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task GetBatchDelegatesToInnerCollectionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var keys = new[] { "key1", "key2" };
        var records = new[] { "record1", "record2" }.ToAsyncEnumerable();
        innerCollection.Setup(c => c.GetBatchAsync(keys, null, default)).Returns(records);
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        var results = collection.GetBatchAsync(keys);
        var resultList = await results.ToListAsync();

        // Assert
        Assert.Equal(new[] { "record1", "record2" }, resultList);
        innerCollection.Verify(c => c.GetBatchAsync(keys, null, default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "GetBatchAsync invoked. Collection Name: testCollection. Keys: key1,key2.");
            AssertLog(logger.Logs, LogLevel.Trace, "GetBatchAsync completed. Collection Name: testCollection. Keys: key1,key2.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "GetBatchAsync invoked. Collection Name: testCollection.");
            AssertLog(logger.Logs, LogLevel.Debug, "GetBatchAsync completed. Collection Name: testCollection.");
        }
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task GetBatchLogsCancellationAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var keys = new[] { "key1", "key2" };
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        static async IAsyncEnumerable<string> CanceledEnumerable([EnumeratorCancellation] CancellationToken cancellationToken)
        {
            yield return "record1";
            await Task.Delay(1, cancellationToken);
            yield return "record2";
        }
        innerCollection.Setup(c => c.GetBatchAsync(keys, null, cts.Token)).Returns(CanceledEnumerable(cts.Token));
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var results = collection.GetBatchAsync(keys, null, cts.Token);
        var enumerator = results.GetAsyncEnumerator(cts.Token);

        Assert.True(await enumerator.MoveNextAsync());
        Assert.Equal("record1", enumerator.Current);

        await AssertThrowsAsync<TaskCanceledException, bool>(enumerator.MoveNextAsync);
        innerCollection.Verify(c => c.GetBatchAsync(keys, null, cts.Token), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "GetBatchAsync invoked. Collection Name: testCollection. Keys: key1,key2.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "GetBatchAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Debug, "GetBatchAsync canceled. Collection Name: testCollection.");
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task GetBatchLogsExceptionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var keys = new[] { "key1", "key2" };
        innerCollection.Setup(c => c.GetBatchAsync(keys, null, default))
                       .Throws(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await AssertThrowsAsync<InvalidOperationException, List<string>>(() => collection.GetBatchAsync(keys).ToListAsync());
        innerCollection.Verify(c => c.GetBatchAsync(keys, null, default), Times.Once());

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "GetBatchAsync invoked. Collection Name: testCollection. Keys: key1,key2.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "GetBatchAsync invoked. Collection Name: testCollection.");
        }

        AssertLog(logger.Logs, LogLevel.Error, "GetBatchAsync failed. Collection Name: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task UpsertDelegatesToInnerCollectionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.UpsertAsync("record1", default)).ReturnsAsync("key1");
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        var result = await collection.UpsertAsync("record1");

        // Assert
        Assert.Equal("key1", result);
        innerCollection.Verify(c => c.UpsertAsync("record1", default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertAsync invoked. Collection name: testCollection.");

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "UpsertAsync completed. Collection name: testCollection. Key: key1.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "UpsertAsync completed. Collection name: testCollection.");
        }
    }

    [Fact]
    public async Task UpsertLogsCancellationAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.UpsertAsync("record1", cts.Token))
                       .Returns(Task.FromCanceled<string>(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.UpsertAsync("record1", cts.Token));
        innerCollection.Verify(c => c.UpsertAsync("record1", cts.Token), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertAsync canceled. Collection name: testCollection.");
    }

    [Fact]
    public async Task UpsertLogsExceptionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        innerCollection.Setup(c => c.UpsertAsync("record1", default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.UpsertAsync("record1"));
        innerCollection.Verify(c => c.UpsertAsync("record1", default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "UpsertAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Error, "UpsertAsync failed. CollectionName: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Theory]
    [InlineData(LogLevel.Debug)]
    [InlineData(LogLevel.Trace)]
    public async Task UpsertBatchDelegatesToInnerCollectionAsync(LogLevel logLevel)
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger(logLevel);
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var records = new[] { "record1", "record2" };
        var keys = new[] { "key1", "key2" }.ToAsyncEnumerable();
        innerCollection.Setup(c => c.UpsertBatchAsync(records, default)).Returns(keys);
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        var results = collection.UpsertBatchAsync(records);
        var resultList = await results.ToListAsync();

        // Assert
        Assert.Equal(new[] { "key1", "key2" }, resultList);
        innerCollection.Verify(c => c.UpsertBatchAsync(records, default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertBatchAsync invoked. Collection name: testCollection.");

        if (logLevel == LogLevel.Trace)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "UpsertBatchAsync completed. Collection name: testCollection. Keys: key1,key2.");
        }
        else
        {
            AssertLog(logger.Logs, LogLevel.Debug, "UpsertBatchAsync completed. Collection name: testCollection.");
        }
    }

    [Fact]
    public async Task UpsertBatchLogsCancellationAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var records = new[] { "record1", "record2" };
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        async IAsyncEnumerable<string> CanceledEnumerable([EnumeratorCancellation] CancellationToken cancellationToken)
        {
            yield return "key1";
            await Task.Delay(1, cancellationToken);
            yield return "key2";
        }
        innerCollection.Setup(c => c.UpsertBatchAsync(records, cts.Token)).Returns(CanceledEnumerable(cts.Token));
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var results = collection.UpsertBatchAsync(records, cts.Token);
        var enumerator = results.GetAsyncEnumerator(cts.Token);
        Assert.True(await enumerator.MoveNextAsync());
        Assert.Equal("key1", enumerator.Current);
        await AssertThrowsAsync<TaskCanceledException, bool>(enumerator.MoveNextAsync);
        innerCollection.Verify(c => c.UpsertBatchAsync(records, cts.Token), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertBatchAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertBatchAsync canceled. Collection name: testCollection.");
    }

    [Fact]
    public async Task UpsertBatchLogsExceptionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var records = new[] { "record1", "record2" };

        innerCollection.Setup(c => c.UpsertBatchAsync(records, default))
                       .Throws(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await AssertThrowsAsync<InvalidOperationException, List<string>>(() => collection.UpsertBatchAsync(records).ToListAsync());
        innerCollection.Verify(c => c.UpsertBatchAsync(records, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "UpsertBatchAsync invoked. Collection name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Error, "UpsertBatchAsync failed. CollectionName: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }

    [Fact]
    public async Task VectorizedSearchDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var vector = new float[] { 1.0f };
        var searchResults = new VectorSearchResults<string>(new[] { new VectorSearchResult<string>("record1", 0.9f) }.ToAsyncEnumerable());
        innerCollection.Setup(c => c.VectorizedSearchAsync(vector, null, default)).ReturnsAsync(searchResults);
        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act
        var result = await collection.VectorizedSearchAsync(vector);

        // Assert
        Assert.Same(searchResults, result);
        innerCollection.Verify(c => c.VectorizedSearchAsync(vector, null, default), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync invoked. Collection Name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync completed. Collection Name: testCollection.");
    }

    [Fact]
    public async Task VectorizedSearchLogsCancellationAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var vector = new float[] { 1.0f };
        using var cts = new CancellationTokenSource();
        cts.Cancel();
        innerCollection.Setup(c => c.VectorizedSearchAsync(vector, null, cts.Token))
                       .Returns(Task.FromCanceled<VectorSearchResults<string>>(cts.Token));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() => collection.VectorizedSearchAsync(vector, null, cts.Token));
        innerCollection.Verify(c => c.VectorizedSearchAsync(vector, null, cts.Token), Times.Once());
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync invoked. Collection Name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync canceled. Collection Name: testCollection.");
    }

    [Fact]
    public async Task VectorizedSearchLogsExceptionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, string>>();
        var logger = new FakeLogger();
        innerCollection.Setup(c => c.CollectionName).Returns("testCollection");
        var vector = new float[] { 1.0f };
        innerCollection.Setup(c => c.VectorizedSearchAsync(vector, null, default))
                       .ThrowsAsync(new InvalidOperationException("Test exception"));

        var collection = new LoggingVectorStoreRecordCollection<string, string>(innerCollection.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.VectorizedSearchAsync(vector));
        innerCollection.Verify(c => c.VectorizedSearchAsync(vector, null, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync invoked. Collection Name: testCollection.");
        AssertLog(logger.Logs, LogLevel.Error, "VectorizedSearchAsync failed. Collection Name: testCollection.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }
}
