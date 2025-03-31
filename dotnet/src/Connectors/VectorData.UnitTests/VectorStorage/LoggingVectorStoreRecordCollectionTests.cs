// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingVectorStoreRecordCollectionTests
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
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        innerCollection.Setup(c => c.CollectionName).Returns("test");
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var name = decorator.CollectionName;

        // Assert
        Assert.Equal("test", name);
        innerCollection.Verify(c => c.CollectionName, Times.Once());
    }

    [Fact]
    public async Task CollectionExistsDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        innerCollection.Setup(c => c.CollectionExistsAsync(default)).ReturnsAsync(true);
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var exists = await decorator.CollectionExistsAsync();

        // Assert
        Assert.True(exists);
        innerCollection.Verify(c => c.CollectionExistsAsync(default), Times.Once());
    }

    [Fact]
    public async Task CreateCollectionDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        innerCollection.Setup(c => c.CreateCollectionAsync(default)).Returns(Task.CompletedTask);
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.CreateCollectionAsync();

        // Assert
        innerCollection.Verify(c => c.CreateCollectionAsync(default), Times.Once());
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        innerCollection.Setup(c => c.CreateCollectionIfNotExistsAsync(default)).Returns(Task.CompletedTask);
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.CreateCollectionIfNotExistsAsync();

        // Assert
        innerCollection.Verify(c => c.CreateCollectionIfNotExistsAsync(default), Times.Once());
    }

    [Fact]
    public async Task DeleteDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        innerCollection.Setup(c => c.DeleteAsync("key", default)).Returns(Task.CompletedTask);
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.DeleteAsync("key");

        // Assert
        innerCollection.Verify(c => c.DeleteAsync("key", default), Times.Once());
    }

    [Fact]
    public async Task DeleteBatchDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        var keys = new[] { "key1", "key2" };
        innerCollection.Setup(c => c.DeleteAsync(keys, default)).Returns(Task.CompletedTask);
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.DeleteAsync(keys);

        // Assert
        innerCollection.Verify(c => c.DeleteAsync(keys, default), Times.Once());
    }

    [Fact]
    public async Task DeleteCollectionDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        innerCollection.Setup(c => c.DeleteCollectionAsync(default)).Returns(Task.CompletedTask);
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        await decorator.DeleteCollectionAsync();

        // Assert
        innerCollection.Verify(c => c.DeleteCollectionAsync(default), Times.Once());
    }

    [Fact]
    public async Task GetDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        var record = new object();
        innerCollection.Setup(c => c.GetAsync("key", null, default)).ReturnsAsync(record);

        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var result = await decorator.GetAsync("key");

        // Assert
        Assert.Same(record, result);
        innerCollection.Verify(c => c.GetAsync("key", null, default), Times.Once());
    }

    [Fact]
    public async Task GetBatchDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        var keys = new[] { "key1", "key2" };
        var records = new[] { new object(), new object() };
        innerCollection.Setup(c => c.GetAsync(keys, null, default)).Returns(records.ToAsyncEnumerable());
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var result = await decorator.GetAsync(keys).ToListAsync();

        // Assert
        Assert.Equal(records, result);
        innerCollection.Verify(c => c.GetAsync(keys, null, default), Times.Once());
    }

    [Fact]
    public async Task UpsertDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        var record = new object();
        innerCollection.Setup(c => c.UpsertAsync(record, default)).ReturnsAsync("key");
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var key = await decorator.UpsertAsync(record);

        // Assert
        Assert.Equal("key", key);
        innerCollection.Verify(c => c.UpsertAsync(record, default), Times.Once());
    }

    [Fact]
    public async Task UpsertBatchDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        var records = new[] { new object(), new object() };
        var keys = new[] { "key1", "key2" };
        innerCollection.Setup(c => c.UpsertAsync(records, default)).Returns(keys.ToAsyncEnumerable());
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var result = await decorator.UpsertAsync(records).ToListAsync();

        // Assert
        Assert.Equal(keys, result);
        innerCollection.Verify(c => c.UpsertAsync(records, default), Times.Once());
    }

    [Fact]
    public async Task VectorizedSearchDelegatesToInnerCollectionAsync()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        var vector = new float[] { 1.0f };
        var options = new VectorSearchOptions<object>();
        var searchResults = new[] { new VectorSearchResult<object>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<object>(searchResults);
        innerCollection.Setup(c => c.VectorizedSearchAsync(vector, options, default)).ReturnsAsync(results);
        var logger = new Mock<ILogger>().Object;
        var decorator = new LoggingVectorStoreRecordCollection<string, object>(innerCollection.Object, logger);

        // Act
        var actualResults = await decorator.VectorizedSearchAsync(vector, options);

        // Assert
        Assert.Same(results, actualResults);
        innerCollection.Verify(c => c.VectorizedSearchAsync(vector, options, default), Times.Once());
    }
}
