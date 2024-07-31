// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for the <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> class.
/// </summary>
public class VolatileVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";
    private const string TestRecordKey1 = "testid1";
    private const string TestRecordKey2 = "testid2";
    private const int TestRecordIntKey1 = 1;
    private const int TestRecordIntKey2 = 2;

    private readonly CancellationToken _testCancellationToken = new(false);

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _collectionStore;

    public VolatileVectorStoreRecordCollectionTests()
    {
        this._collectionStore = new();
    }

    [Theory]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        var collection = new ConcurrentDictionary<object, object>();
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = new VolatileVectorStoreRecordCollection<string, SinglePropsModel<string>>(
            this._collectionStore,
            collectionName);

        // Act
        var actual = await sut.CollectionExistsAsync(this._testCancellationToken);

        // Assert
        Assert.Equal(expectedExists, actual);
    }

    [Fact]
    public async Task CanCreateCollectionAsync()
    {
        // Arrange
        var sut = this.CreateRecordCollection<string>(false);

        // Act
        await sut.CreateCollectionAsync(this._testCancellationToken);

        // Assert
        Assert.True(this._collectionStore.ContainsKey(TestCollectionName));
    }

    [Fact]
    public async Task DeleteCollectionRemovesCollectionFromDictionaryAsync()
    {
        // Arrange
        var collection = new ConcurrentDictionary<object, object>();
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<string>(false);

        // Act
        await sut.DeleteCollectionAsync(this._testCancellationToken);

        // Assert
        Assert.Empty(this._collectionStore);
    }

    [Theory]
    [InlineData(true, TestRecordKey1)]
    [InlineData(true, TestRecordIntKey1)]
    [InlineData(false, TestRecordKey1)]
    [InlineData(false, TestRecordIntKey1)]
    public async Task CanGetRecordWithVectorsAsync<TKey>(bool useDefinition, TKey testKey)
        where TKey : notnull
    {
        // Arrange
        var record = CreateModel(testKey, withVectors: true);
        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(testKey!, record);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        var actual = await sut.GetAsync(
            testKey,
            new()
            {
                IncludeVectors = true
            },
            this._testCancellationToken);

        // Assert
        var expectedArgs = new object[] { TestRecordKey1 };

        Assert.NotNull(actual);
        Assert.Equal(testKey, actual.Key);
        Assert.Equal($"data {testKey}", actual.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
    }

    [Theory]
    [InlineData(true, TestRecordKey1, TestRecordKey2)]
    [InlineData(true, TestRecordIntKey1, TestRecordIntKey2)]
    [InlineData(false, TestRecordKey1, TestRecordKey2)]
    [InlineData(false, TestRecordIntKey1, TestRecordIntKey2)]
    public async Task CanGetManyRecordsWithVectorsAsync<TKey>(bool useDefinition, TKey testKey1, TKey testKey2)
        where TKey : notnull
    {
        // Arrange
        var record1 = CreateModel(testKey1, withVectors: true);
        var record2 = CreateModel(testKey2, withVectors: true);
        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(testKey1!, record1);
        collection.TryAdd(testKey2!, record2);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        var actual = await sut.GetBatchAsync(
            [testKey1, testKey2],
            new()
            {
                IncludeVectors = true
            },
            this._testCancellationToken).ToListAsync();

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(testKey1, actual[0].Key);
        Assert.Equal($"data {testKey1}", actual[0].Data);
        Assert.Equal(testKey2, actual[1].Key);
        Assert.Equal($"data {testKey2}", actual[1].Data);
    }

    [Theory]
    [InlineData(true, TestRecordKey1, TestRecordKey2)]
    [InlineData(true, TestRecordIntKey1, TestRecordIntKey2)]
    [InlineData(false, TestRecordKey1, TestRecordKey2)]
    [InlineData(false, TestRecordIntKey1, TestRecordIntKey2)]
    public async Task CanDeleteRecordAsync<TKey>(bool useDefinition, TKey testKey1, TKey testKey2)
        where TKey : notnull
    {
        // Arrange
        var record1 = CreateModel(testKey1, withVectors: true);
        var record2 = CreateModel(testKey2, withVectors: true);
        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(testKey1, record1);
        collection.TryAdd(testKey2, record2);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        await sut.DeleteAsync(
            testKey1,
            cancellationToken: this._testCancellationToken);

        // Assert
        Assert.False(collection.ContainsKey(testKey1));
        Assert.True(collection.ContainsKey(testKey2));
    }

    [Theory]
    [InlineData(true, TestRecordKey1, TestRecordKey2)]
    [InlineData(true, TestRecordIntKey1, TestRecordIntKey2)]
    [InlineData(false, TestRecordKey1, TestRecordKey2)]
    [InlineData(false, TestRecordIntKey1, TestRecordIntKey2)]
    public async Task CanDeleteManyRecordsWithVectorsAsync<TKey>(bool useDefinition, TKey testKey1, TKey testKey2)
        where TKey : notnull
    {
        // Arrange
        var record1 = CreateModel(testKey1, withVectors: true);
        var record2 = CreateModel(testKey2, withVectors: true);
        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(testKey1, record1);
        collection.TryAdd(testKey2, record2);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        await sut.DeleteBatchAsync(
            [testKey1, testKey2],
            cancellationToken: this._testCancellationToken);

        // Assert
        Assert.False(collection.ContainsKey(testKey1));
        Assert.False(collection.ContainsKey(testKey2));
    }

    [Theory]
    [InlineData(true, TestRecordKey1)]
    [InlineData(true, TestRecordIntKey1)]
    [InlineData(false, TestRecordKey1)]
    [InlineData(false, TestRecordIntKey1)]
    public async Task CanUpsertRecordAsync<TKey>(bool useDefinition, TKey testKey1)
        where TKey : notnull
    {
        // Arrange
        var record1 = CreateModel(testKey1, withVectors: true);
        var collection = new ConcurrentDictionary<object, object>();
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        var upsertResult = await sut.UpsertAsync(
            record1,
            cancellationToken: this._testCancellationToken);

        // Assert
        Assert.Equal(testKey1, upsertResult);
        Assert.True(collection.ContainsKey(testKey1));
        Assert.IsType<SinglePropsModel<TKey>>(collection[testKey1]);
        Assert.Equal($"data {testKey1}", (collection[testKey1] as SinglePropsModel<TKey>)!.Data);
    }

    [Theory]
    [InlineData(true, TestRecordKey1, TestRecordKey2)]
    [InlineData(true, TestRecordIntKey1, TestRecordIntKey2)]
    [InlineData(false, TestRecordKey1, TestRecordKey2)]
    [InlineData(false, TestRecordIntKey1, TestRecordIntKey2)]
    public async Task CanUpsertManyRecordsAsync<TKey>(bool useDefinition, TKey testKey1, TKey testKey2)
        where TKey : notnull
    {
        // Arrange
        var record1 = CreateModel(testKey1, withVectors: true);
        var record2 = CreateModel(testKey2, withVectors: true);

        var collection = new ConcurrentDictionary<object, object>();
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        var actual = await sut.UpsertBatchAsync(
            [record1, record2],
            cancellationToken: this._testCancellationToken).ToListAsync();

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(testKey1, actual[0]);
        Assert.Equal(testKey2, actual[1]);

        Assert.True(collection.ContainsKey(testKey1));
        Assert.IsType<SinglePropsModel<TKey>>(collection[testKey1]);
        Assert.Equal($"data {testKey1}", (collection[testKey1] as SinglePropsModel<TKey>)!.Data);
    }

    private static SinglePropsModel<TKey> CreateModel<TKey>(TKey key, bool withVectors)
    {
        return new SinglePropsModel<TKey>
        {
            Key = key,
            Data = "data " + key,
            Vector = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            NotAnnotated = null,
        };
    }

    private VolatileVectorStoreRecordCollection<TKey, SinglePropsModel<TKey>> CreateRecordCollection<TKey>(bool useDefinition)
        where TKey : notnull
    {
        return new VolatileVectorStoreRecordCollection<TKey, SinglePropsModel<TKey>>(
            this._collectionStore,
            TestCollectionName,
            new()
            {
                VectorStoreRecordDefinition = useDefinition ? this._singlePropsDefinition : null
            });
    }

    private readonly VectorStoreRecordDefinition _singlePropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data", typeof(string)),
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>))
        ]
    };

    public sealed class SinglePropsModel<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; }

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
