// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
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
    public void GetCollectionDelegatesToInnerStore()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>();
        var logger = new Mock<ILogger>().Object;
        var collection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        innerStore.Setup(s => s.GetCollection<string, object>("test", null))
                  .Returns(collection);
        var decorator = new LoggingVectorStore(innerStore.Object, logger);

        // Act
        var result = decorator.GetCollection<string, object>("test");

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
        string[] names = ["collection-1", "collection-2"];
        innerStore.Setup(s => s.ListCollectionNamesAsync(default))
                  .Returns(names.ToAsyncEnumerable());
        var decorator = new LoggingVectorStore(innerStore.Object, logger);

        // Act
        var result = await decorator.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(names, result);
        innerStore.Verify(s => s.ListCollectionNamesAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Retrieved collection: 'collection-1'");
        AssertLog(logger.Logs, LogLevel.Trace, "Retrieved collection: 'collection-2'");
        AssertLog(logger.Logs, LogLevel.Debug, "ListCollectionNamesAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "ListCollectionNamesAsync completed.");
    }
}
