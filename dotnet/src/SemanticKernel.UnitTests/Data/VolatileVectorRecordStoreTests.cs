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
/// Contains tests for the <see cref="VolatileVectorRecordStore{TRecord}"/> class.
/// </summary>
public class VolatileVectorRecordStoreTests
{
    private const string TestCollectionName = "testcollection";
    private const string TestRecordKey1 = "testid1";
    private const string TestRecordKey2 = "testid2";

    private readonly CancellationToken _testCancellationToken = new(false);

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, SinglePropsModel>> _collectionStore;

    public VolatileVectorRecordStoreTests()
    {
        this._collectionStore = new();
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanGetRecordWithVectorsAsync(bool useDefinition, bool passCollectionToMethod)
    {
        // Arrange
        var record = CreateModel(TestRecordKey1, withVectors: true);
        var collection = new ConcurrentDictionary<string, SinglePropsModel>();
        collection.TryAdd(TestRecordKey1, record);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateVectorRecordStore(useDefinition, passCollectionToMethod);

        // Act
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new()
            {
                IncludeVectors = true,
                CollectionName = passCollectionToMethod ? TestCollectionName : null
            },
            this._testCancellationToken);

        // Assert
        var expectedArgs = new object[] { TestRecordKey1 };

        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data testid1", actual.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanGetManyRecordsWithVectorsAsync(bool useDefinition, bool passCollectionToMethod)
    {
        // Arrange
        var record1 = CreateModel(TestRecordKey1, withVectors: true);
        var record2 = CreateModel(TestRecordKey2, withVectors: true);
        var collection = new ConcurrentDictionary<string, SinglePropsModel>();
        collection.TryAdd(TestRecordKey1, record1);
        collection.TryAdd(TestRecordKey2, record2);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateVectorRecordStore(useDefinition, passCollectionToMethod);

        // Act
        var actual = await sut.GetBatchAsync(
            [TestRecordKey1, TestRecordKey2],
            new()
            {
                IncludeVectors = true,
                CollectionName = passCollectionToMethod ? TestCollectionName : null
            },
            this._testCancellationToken).ToListAsync();

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0].Key);
        Assert.Equal("data testid1", actual[0].Data);
        Assert.Equal(TestRecordKey2, actual[1].Key);
        Assert.Equal("data testid2", actual[1].Data);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanDeleteRecordAsync(bool useDefinition, bool passCollectionToMethod)
    {
        // Arrange
        var record1 = CreateModel(TestRecordKey1, withVectors: true);
        var record2 = CreateModel(TestRecordKey2, withVectors: true);
        var collection = new ConcurrentDictionary<string, SinglePropsModel>();
        collection.TryAdd(TestRecordKey1, record1);
        collection.TryAdd(TestRecordKey2, record2);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateVectorRecordStore(useDefinition, passCollectionToMethod);

        // Act
        await sut.DeleteAsync(
            TestRecordKey1,
            new()
            {
                CollectionName = passCollectionToMethod ? TestCollectionName : null
            },
            this._testCancellationToken);

        // Assert
        Assert.False(collection.ContainsKey(TestRecordKey1));
        Assert.True(collection.ContainsKey(TestRecordKey2));
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanDeleteManyRecordsWithVectorsAsync(bool useDefinition, bool passCollectionToMethod)
    {
        // Arrange
        var record1 = CreateModel(TestRecordKey1, withVectors: true);
        var record2 = CreateModel(TestRecordKey2, withVectors: true);
        var collection = new ConcurrentDictionary<string, SinglePropsModel>();
        collection.TryAdd(TestRecordKey1, record1);
        collection.TryAdd(TestRecordKey2, record2);
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateVectorRecordStore(useDefinition, passCollectionToMethod);

        // Act
        await sut.DeleteBatchAsync(
            [TestRecordKey1, TestRecordKey2],
            new()
            {
                CollectionName = passCollectionToMethod ? TestCollectionName : null
            },
            this._testCancellationToken);

        // Assert
        Assert.False(collection.ContainsKey(TestRecordKey1));
        Assert.False(collection.ContainsKey(TestRecordKey2));
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanUpsertRecordAsync(bool useDefinition, bool passCollectionToMethod)
    {
        // Arrange
        var record1 = CreateModel(TestRecordKey1, withVectors: true);
        var collection = new ConcurrentDictionary<string, SinglePropsModel>();
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateVectorRecordStore(useDefinition, passCollectionToMethod);

        // Act
        var upsertResult = await sut.UpsertAsync(
            record1,
            new()
            {
                CollectionName = passCollectionToMethod ? TestCollectionName : null
            },
            this._testCancellationToken);

        // Assert
        Assert.Equal(TestRecordKey1, upsertResult);
        Assert.True(collection.ContainsKey(TestRecordKey1));
        Assert.Equal("data testid1", collection[TestRecordKey1].Data);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanUpsertManyRecordsAsync(bool useDefinition, bool passCollectionToMethod)
    {
        // Arrange
        var record1 = CreateModel(TestRecordKey1, withVectors: true);
        var record2 = CreateModel(TestRecordKey2, withVectors: true);

        var collection = new ConcurrentDictionary<string, SinglePropsModel>();
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateVectorRecordStore(useDefinition, passCollectionToMethod);

        // Act
        var actual = await sut.UpsertBatchAsync(
            [record1, record2],
            new()
            {
                CollectionName = passCollectionToMethod ? TestCollectionName : null
            },
            this._testCancellationToken).ToListAsync();

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0]);
        Assert.Equal(TestRecordKey2, actual[1]);

        Assert.True(collection.ContainsKey(TestRecordKey1));
        Assert.Equal("data testid1", collection[TestRecordKey1].Data);
    }

    private static SinglePropsModel CreateModel(string key, bool withVectors)
    {
        return new SinglePropsModel
        {
            Key = key,
            Data = "data " + key,
            Vector = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            NotAnnotated = null,
        };
    }

    private VolatileVectorRecordStore<SinglePropsModel> CreateVectorRecordStore(bool useDefinition, bool passCollectionToMethod)
    {
        return new VolatileVectorRecordStore<SinglePropsModel>(
            this._collectionStore,
            new()
            {
                DefaultCollectionName = passCollectionToMethod ? null : TestCollectionName,
                VectorStoreRecordDefinition = useDefinition ? this._singlePropsDefinition : null
            });
    }

    private readonly VectorStoreRecordDefinition _singlePropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key"),
            new VectorStoreRecordDataProperty("Data"),
            new VectorStoreRecordVectorProperty("Vector")
        ]
    };

    public sealed class SinglePropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
