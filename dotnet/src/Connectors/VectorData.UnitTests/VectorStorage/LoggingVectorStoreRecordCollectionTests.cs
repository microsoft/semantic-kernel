// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
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
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorStoreRecordCollection<string, object>(null!, logger));
    }

    [Fact]
    public void ConstructorThrowsOnNullLogger()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorStoreRecordCollection<string, object>(innerCollection, null!));
    }

    [Fact]
    public void CollectionNameReturnsInnerCollectionName()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var name = decorator.CollectionName;

        // Assert
        Assert.Equal("test-collection", name);
        innerCollection.Verify(c => c.CollectionName, Times.Once());
    }

    [Fact]
    public async Task CollectionExistsDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        innerCollection.Setup(c => c.CollectionExistsAsync(default)).ReturnsAsync(true);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var exists = await decorator.CollectionExistsAsync();

        // Assert
        Assert.True(exists);
        innerCollection.Verify(c => c.CollectionExistsAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Collection 'test-collection' exists: True");
        AssertLog(logger.Logs, LogLevel.Debug, "CollectionExistsAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "CollectionExistsAsync completed.");
    }

    [Fact]
    public async Task CreateCollectionDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        innerCollection.Setup(c => c.CreateCollectionAsync(default)).Returns(Task.CompletedTask);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.CreateCollectionAsync();

        // Assert
        innerCollection.Verify(c => c.CreateCollectionAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Creating a collection 'test-collection'");
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionAsync completed.");
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        innerCollection.Setup(c => c.CreateCollectionIfNotExistsAsync(default)).Returns(Task.CompletedTask);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.CreateCollectionIfNotExistsAsync();

        // Assert
        innerCollection.Verify(c => c.CreateCollectionIfNotExistsAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionIfNotExistsAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "CreateCollectionIfNotExistsAsync completed.");
    }

    [Fact]
    public async Task DeleteDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        innerCollection.Setup(c => c.DeleteAsync("key", default)).Returns(Task.CompletedTask);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.DeleteAsync("key");

        // Assert
        innerCollection.Verify(c => c.DeleteAsync("key", default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Deleting a record from 'test-collection' with key");
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteAsync completed.");
    }

    [Fact]
    public async Task DeleteBatchDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        var keys = new[] { "key1", "key2" };
        innerCollection.Setup(c => c.DeleteBatchAsync(keys, default)).Returns(Task.CompletedTask);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.DeleteBatchAsync(keys);

        // Assert
        innerCollection.Verify(c => c.DeleteBatchAsync(keys, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Deleting records from 'test-collection' with keys");
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteBatchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteBatchAsync completed.");
    }

    [Fact]
    public async Task DeleteCollectionDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        innerCollection.Setup(c => c.DeleteCollectionAsync(default)).Returns(Task.CompletedTask);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.DeleteCollectionAsync();

        // Assert
        innerCollection.Verify(c => c.DeleteCollectionAsync(default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "DeleteCollectionAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "DeleteCollectionAsync completed.");
    }

    [Fact]
    public async Task GetDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        var record = new object();
        innerCollection.Setup(c => c.GetAsync("key", null, default)).ReturnsAsync(record);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var result = await decorator.GetAsync("key");

        // Assert
        Assert.Same(record, result);
        innerCollection.Verify(c => c.GetAsync("key", null, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Getting a record from 'test-collection' with key");
        AssertLog(logger.Logs, LogLevel.Trace, "Retrieved record from 'test-collection'");
        AssertLog(logger.Logs, LogLevel.Debug, "GetAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "GetAsync completed.");
    }

    [Fact]
    public async Task GetBatchDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        var keys = new[] { "key1", "key2" };
        var records = new[] { new object(), new object() };
        innerCollection.Setup(c => c.GetBatchAsync(keys, null, default)).Returns(records.ToAsyncEnumerable());
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var result = await decorator.GetBatchAsync(keys).ToListAsync();

        // Assert
        Assert.Equal(records, result);
        innerCollection.Verify(c => c.GetBatchAsync(keys, null, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "GetBatchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "GetBatchAsync completed.");

        foreach (var record in records)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "Retrieved record from 'test-collection'");
        }
    }

    [Fact]
    public async Task UpsertDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        var record = new object();
        innerCollection.Setup(c => c.UpsertAsync(record, default)).ReturnsAsync("key");
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var key = await decorator.UpsertAsync(record);

        // Assert
        Assert.Equal("key", key);
        innerCollection.Verify(c => c.UpsertAsync(record, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Upserting a record in 'test-collection'");
        AssertLog(logger.Logs, LogLevel.Trace, "Upserted record in 'test-collection' with key");
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertAsync completed.");
    }

    [Fact]
    public async Task UpsertBatchDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        var records = new[] { new object(), new object() };
        var keys = new[] { "key1", "key2" };
        innerCollection.Setup(c => c.UpsertBatchAsync(records, default)).Returns(keys.ToAsyncEnumerable());
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var result = await decorator.UpsertBatchAsync(records).ToListAsync();

        // Assert
        Assert.Equal(keys, result);
        innerCollection.Verify(c => c.UpsertBatchAsync(records, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Upserting records in 'test-collection'");
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertBatchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "UpsertBatchAsync completed.");

        foreach (var key in keys)
        {
            AssertLog(logger.Logs, LogLevel.Trace, "Upserted record in 'test-collection' with key");
        }
    }

    [Fact]
    public async Task VectorizedSearchDelegatesToInnerCollectionAndLogsAsync()
    {
        // Arrange
        var innerCollection = GetMockCollection();
        var vector = new float[] { 1.0f };
        var options = new VectorSearchOptions<object>();
        var searchResults = new[] { new VectorSearchResult<object>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<object>(searchResults) { TotalCount = 1 };
        innerCollection.Setup(c => c.VectorizedSearchAsync(vector, options, default)).ReturnsAsync(results);
        var logger = new FakeLogger();
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var actualResults = await decorator.VectorizedSearchAsync(vector, options);

        // Assert
        Assert.Same(results, actualResults);
        innerCollection.Verify(c => c.VectorizedSearchAsync(vector, options, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Trace, "Found 1 record(s) in 'test-collection' using vector search.");
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync completed.");
    }

    #region private

    private static Mock<IVectorStoreRecordCollection<string, object>> GetMockCollection()
    {
        var collection = new Mock<IVectorStoreRecordCollection<string, object>>();

        collection.Setup(c => c.CollectionName).Returns("test-collection");

        return collection;
    }

    #endregion
}
