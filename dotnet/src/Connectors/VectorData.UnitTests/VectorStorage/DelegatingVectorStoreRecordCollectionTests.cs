// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests.VectorStorage;

public class DelegatingVectorStoreRecordCollectionTests
{
    private readonly Mock<IVectorStoreRecordCollection<string, object>> _mockInnerCollection;
    private readonly FakeVectorStoreRecordCollection<string, object> _delegatingCollection;

    public DelegatingVectorStoreRecordCollectionTests()
    {
        this._mockInnerCollection = new Mock<IVectorStoreRecordCollection<string, object>>();
        this._delegatingCollection = new FakeVectorStoreRecordCollection<string, object>(this._mockInnerCollection.Object);
    }

    [Fact]
    public void ConstructorWithNullInnerCollectionThrowsArgumentNullException()
    {
        Assert.Throws<ArgumentNullException>(() => new FakeVectorStoreRecordCollection<string, object>(null!));
    }

    [Fact]
    public void CollectionNameCallsInnerCollection()
    {
        this._mockInnerCollection.Setup(c => c.CollectionName).Returns("test-collection");

        var result = this._delegatingCollection.CollectionName;

        Assert.Equal("test-collection", result);
        this._mockInnerCollection.Verify(x => x.CollectionName, Times.Once);
    }

    [Fact]
    public async Task CollectionExistsCallsInnerCollectionAsync()
    {
        this._mockInnerCollection.Setup(c => c.CollectionExistsAsync(default)).ReturnsAsync(true);

        var result = await this._delegatingCollection.CollectionExistsAsync();

        Assert.True(result);
        this._mockInnerCollection.Verify(x => x.CollectionExistsAsync(default), Times.Once);
    }

    [Fact]
    public async Task CreateCollectionCallsInnerCollectionAsync()
    {
        await this._delegatingCollection.CreateCollectionAsync();
        this._mockInnerCollection.Verify(x => x.CreateCollectionAsync(default), Times.Once);
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsCallsInnerCollectionAsync()
    {
        await this._delegatingCollection.CreateCollectionIfNotExistsAsync();
        this._mockInnerCollection.Verify(x => x.CreateCollectionIfNotExistsAsync(default), Times.Once);
    }

    [Fact]
    public async Task DeleteCollectionCallsInnerCollectionAsync()
    {
        await this._delegatingCollection.DeleteCollectionAsync();
        this._mockInnerCollection.Verify(x => x.DeleteCollectionAsync(default), Times.Once);
    }

    [Fact]
    public async Task GetAsyncCallsInnerCollectionAsync()
    {
        var key = "test-key";
        var options = new GetRecordOptions();
        var record = new object();

        this._mockInnerCollection.Setup(c => c.GetAsync(key, options, default)).ReturnsAsync(record);

        var result = await this._delegatingCollection.GetAsync(key, options);

        Assert.Equal(record, result);
        this._mockInnerCollection.Verify(x => x.GetAsync(key, options, default), Times.Once);
    }

    [Fact]
    public async Task GetBatchAsyncCallsInnerCollectionAsync()
    {
        var keys = new[] { "key1", "key2" };
        var options = new GetRecordOptions();
        var records = new[] { new object(), new object() };

        this._mockInnerCollection.Setup(c => c.GetBatchAsync(keys, options, default)).Returns(records.ToAsyncEnumerable());

        var result = await this._delegatingCollection.GetBatchAsync(keys, options).ToListAsync();

        Assert.Equal(records, result);
        this._mockInnerCollection.Verify(x => x.GetBatchAsync(keys, options, default), Times.Once);
    }

    [Fact]
    public async Task DeleteAsyncCallsInnerCollectionAsync()
    {
        var key = "test-key";

        await this._delegatingCollection.DeleteAsync(key);
        this._mockInnerCollection.Verify(x => x.DeleteAsync(key, default), Times.Once);
    }

    [Fact]
    public async Task DeleteBatchAsyncCallsInnerCollectionAsync()
    {
        var keys = new[] { "key1", "key2" };

        await this._delegatingCollection.DeleteBatchAsync(keys);
        this._mockInnerCollection.Verify(x => x.DeleteBatchAsync(keys, default), Times.Once);
    }

    [Fact]
    public async Task UpsertAsyncCallsInnerCollectionAsync()
    {
        var record = new object();
        var key = "test-key";

        this._mockInnerCollection.Setup(c => c.UpsertAsync(record, default)).ReturnsAsync(key);

        var result = await this._delegatingCollection.UpsertAsync(record);

        Assert.Equal(key, result);
        this._mockInnerCollection.Verify(x => x.UpsertAsync(record, default), Times.Once);
    }

    [Fact]
    public async Task UpsertBatchAsyncCallsInnerCollectionAsync()
    {
        var records = new[] { new object(), new object() };
        var keys = new[] { "key1", "key2" };

        this._mockInnerCollection.Setup(c => c.UpsertBatchAsync(records, default)).Returns(keys.ToAsyncEnumerable());

        var result = await this._delegatingCollection.UpsertBatchAsync(records).ToListAsync();

        Assert.Equal(keys, result);
        this._mockInnerCollection.Verify(x => x.UpsertBatchAsync(records, default), Times.Once);
    }

    [Fact]
    public async Task VectorizedSearchCallsInnerCollectionAsync()
    {
        var vector = new float[] { 1.0f, 2.0f };
        var options = new VectorSearchOptions<object>();
        var searchResults = new[] { new VectorSearchResult<object>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<object>(searchResults);

        this._mockInnerCollection.Setup(c => c.VectorizedSearchAsync(vector, options, default))
            .ReturnsAsync(results);

        var result = await this._delegatingCollection.VectorizedSearchAsync(vector, options);

        Assert.Equal(results, result);
        this._mockInnerCollection.Verify(x => x.VectorizedSearchAsync(vector, options, default), Times.Once);
    }

    private sealed class FakeVectorStoreRecordCollection<TKey, TRecord> : DelegatingVectorStoreRecordCollection<TKey, TRecord>
        where TKey : notnull
    {
        public FakeVectorStoreRecordCollection(IVectorStoreRecordCollection<TKey, TRecord> innerCollection) : base(innerCollection) { }
    }
}
