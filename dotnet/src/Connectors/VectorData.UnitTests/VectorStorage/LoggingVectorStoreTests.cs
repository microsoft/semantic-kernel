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

public class LoggingVectorStoreTests : BaseLoggingTests
{
    [Fact]
    public void ConstructorThrowsOnNullInnerStore()
    {
        // Arrange
        var logger = new Mock<ILogger>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorStore(null!, logger));
    }

    [Fact]
    public void ConstructorThrowsOnNullLogger()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorStore(innerStore, null!));
    }

    [Fact]
    public void GetCollectionReturnsLoggingDecorator()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>();
        var logger = new Mock<ILogger>().Object;
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;

        innerStore.Setup(s => s.GetCollection<string, object>("test", null))
                  .Returns(innerCollection);

        var store = new LoggingVectorStore(innerStore.Object, logger);

        // Act
        var result = store.GetCollection<string, object>("test");

        // Assert
        Assert.IsType<LoggingVectorStoreRecordCollection<string, object>>(result);
        innerStore.Verify(s => s.GetCollection<string, object>("test", null), Times.Once());
    }

    [Fact]
    public async Task ListCollectionNamesDelegatesToInnerStoreAsync()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>();
        var logger = new FakeLogger();
        var collectionNames = new[] { "collection1", "collection2" }.ToAsyncEnumerable();

        innerStore.Setup(s => s.ListCollectionNamesAsync(default))
                  .Returns(collectionNames);

        var store = new LoggingVectorStore(innerStore.Object, logger);

        // Act
        var results = store.ListCollectionNamesAsync();
        var resultList = await results.ToListAsync();

        // Assert
        Assert.Equal(new[] { "collection1", "collection2" }, resultList);
        innerStore.Verify(s => s.ListCollectionNamesAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "ListCollectionNamesAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "ListCollectionNamesAsync completed. Collections: collection1,collection2");
    }

    [Fact]
    public async Task ListCollectionNamesLogsCancellationAsync()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>();
        var logger = new FakeLogger();

        using var cts = new CancellationTokenSource();
        cts.Cancel();

        // Setup the inner store to yield one item before cancellation
        static async IAsyncEnumerable<string> CanceledEnumerable([EnumeratorCancellation] CancellationToken cancellationToken)
        {
            yield return "collection1";
            await Task.Delay(1, cancellationToken);
            yield return "collection2";
        }

        innerStore.Setup(s => s.ListCollectionNamesAsync(cts.Token))
                  .Returns(CanceledEnumerable(cts.Token));

        var store = new LoggingVectorStore(innerStore.Object, logger);

        // Act & Assert
        var results = store.ListCollectionNamesAsync(cts.Token);
        var enumerator = results.GetAsyncEnumerator(cts.Token);

        Assert.True(await enumerator.MoveNextAsync());
        Assert.Equal("collection1", enumerator.Current);

        await AssertThrowsAsync<TaskCanceledException, bool>(enumerator.MoveNextAsync);

        innerStore.Verify(s => s.ListCollectionNamesAsync(cts.Token), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "ListCollectionNamesAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "ListCollectionNamesAsync canceled.");
    }

    [Fact]
    public async Task ListCollectionNamesLogsExceptionAsync()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>();
        var logger = new FakeLogger();

        innerStore
            .Setup(s => s.ListCollectionNamesAsync(default))
            .Throws(new InvalidOperationException("Test exception"));

        var store = new LoggingVectorStore(innerStore.Object, logger);

        // Act & Assert
        var exception = await AssertThrowsAsync<InvalidOperationException, List<string>>(() =>
            store.ListCollectionNamesAsync().ToListAsync());

        innerStore.Verify(s => s.ListCollectionNamesAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "ListCollectionNamesAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Error, "ListCollectionNamesAsync failed.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }
}
