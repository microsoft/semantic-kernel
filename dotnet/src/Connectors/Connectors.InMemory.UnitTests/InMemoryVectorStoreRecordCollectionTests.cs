// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Xunit;

namespace SemanticKernel.Connectors.InMemory.UnitTests;

/// <summary>
/// Contains tests for the <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> class.
/// </summary>
public class InMemoryVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";
    private const string TestRecordKey1 = "testid1";
    private const string TestRecordKey2 = "testid2";
    private const int TestRecordIntKey1 = 1;
    private const int TestRecordIntKey2 = 2;

    private readonly CancellationToken _testCancellationToken = new(false);

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _collectionStore;
    private readonly ConcurrentDictionary<string, Type> _collectionStoreTypes;

    public InMemoryVectorStoreRecordCollectionTests()
    {
        this._collectionStore = new();
        this._collectionStoreTypes = new();
    }

    [Theory]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        var collection = new ConcurrentDictionary<object, object>();
        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = new InMemoryVectorStoreRecordCollection<string, SinglePropsModel<string>>(
            this._collectionStore,
            this._collectionStoreTypes,
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

    [Theory]
    [InlineData(true, TestRecordKey1, TestRecordKey2)]
    [InlineData(true, TestRecordIntKey1, TestRecordIntKey2)]
    [InlineData(false, TestRecordKey1, TestRecordKey2)]
    [InlineData(false, TestRecordIntKey1, TestRecordIntKey2)]
    public async Task CanSearchWithVectorAsync<TKey>(bool useDefinition, TKey testKey1, TKey testKey2)
        where TKey : notnull
    {
        // Arrange
        var record1 = CreateModel(testKey1, withVectors: true, new float[] { 1, 1, 1, 1 });
        var record2 = CreateModel(testKey2, withVectors: true, new float[] { -1, -1, -1, -1 });

        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(testKey1, record1);
        collection.TryAdd(testKey2, record2);

        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        var actual = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new float[] { 1, 1, 1, 1 }),
            new() { IncludeVectors = true },
            this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        Assert.Null(actual.TotalCount);
        var actualResults = await actual.Results.ToListAsync();
        Assert.Equal(2, actualResults.Count);
        Assert.Equal(testKey1, actualResults[0].Record.Key);
        Assert.Equal($"data {testKey1}", actualResults[0].Record.Data);
        Assert.Equal(1, actualResults[0].Score);
        Assert.Equal(testKey2, actualResults[1].Record.Key);
        Assert.Equal($"data {testKey2}", actualResults[1].Record.Data);
        Assert.Equal(-1, actualResults[1].Score);
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    [Theory]
    [InlineData(true, TestRecordKey1, TestRecordKey2, "Equality")]
    [InlineData(true, TestRecordIntKey1, TestRecordIntKey2, "Equality")]
    [InlineData(false, TestRecordKey1, TestRecordKey2, "Equality")]
    [InlineData(false, TestRecordIntKey1, TestRecordIntKey2, "Equality")]
    [InlineData(true, TestRecordKey1, TestRecordKey2, "TagListContains")]
    [InlineData(true, TestRecordIntKey1, TestRecordIntKey2, "TagListContains")]
    [InlineData(false, TestRecordKey1, TestRecordKey2, "TagListContains")]
    [InlineData(false, TestRecordIntKey1, TestRecordIntKey2, "TagListContains")]
    public async Task CanSearchWithVectorAndFilterAsync<TKey>(bool useDefinition, TKey testKey1, TKey testKey2, string filterType)
        where TKey : notnull
    {
        // Arrange
        var record1 = CreateModel(testKey1, withVectors: true, new float[] { 1, 1, 1, 1 });
        var record2 = CreateModel(testKey2, withVectors: true, new float[] { -1, -1, -1, -1 });

        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(testKey1, record1);
        collection.TryAdd(testKey2, record2);

        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<TKey>(useDefinition);

        // Act
        var filter = filterType == "Equality" ? new VectorSearchFilter().EqualTo("Data", $"data {testKey2}") : new VectorSearchFilter().AnyTagEqualTo("Tags", $"tag {testKey2}");
        var actual = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new float[] { 1, 1, 1, 1 }),
            new() { IncludeVectors = true, OldFilter = filter, IncludeTotalCount = true },
            this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(1, actual.TotalCount);
        var actualResults = await actual.Results.ToListAsync();
        Assert.Single(actualResults);
        Assert.Equal(testKey2, actualResults[0].Record.Key);
        Assert.Equal($"data {testKey2}", actualResults[0].Record.Data);
        Assert.Equal(-1, actualResults[0].Score);
    }
#pragma warning restore CS0618 // Type or member is obsolete

    [Theory]
    [InlineData(DistanceFunction.CosineSimilarity, 1, -1)]
    [InlineData(DistanceFunction.CosineDistance, 0, 2)]
    [InlineData(DistanceFunction.DotProductSimilarity, 4, -4)]
    [InlineData(DistanceFunction.EuclideanDistance, 0, 4)]
    public async Task CanSearchWithDifferentDistanceFunctionsAsync(string distanceFunction, double expectedScoreResult1, double expectedScoreResult2)
    {
        // Arrange
        var record1 = CreateModel(TestRecordKey1, withVectors: true, new float[] { 1, 1, 1, 1 });
        var record2 = CreateModel(TestRecordKey2, withVectors: true, new float[] { -1, -1, -1, -1 });

        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(TestRecordKey1, record1);
        collection.TryAdd(TestRecordKey2, record2);

        this._collectionStore.TryAdd(TestCollectionName, collection);

        VectorStoreRecordDefinition singlePropsDefinition = new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("Data", typeof(string)),
                new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { DistanceFunction = distanceFunction }
            ]
        };

        var sut = new InMemoryVectorStoreRecordCollection<string, SinglePropsModel<string>>(
            this._collectionStore,
            this._collectionStoreTypes,
            TestCollectionName,
            new()
            {
                VectorStoreRecordDefinition = singlePropsDefinition
            });

        // Act
        var actual = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new float[] { 1, 1, 1, 1 }),
            new() { IncludeVectors = true },
            this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        var actualResults = await actual.Results.ToListAsync();
        Assert.Equal(2, actualResults.Count);
        Assert.Equal(TestRecordKey1, actualResults[0].Record.Key);
        Assert.Equal($"data {TestRecordKey1}", actualResults[0].Record.Data);
        Assert.Equal(expectedScoreResult1, actualResults[0].Score);
        Assert.Equal(TestRecordKey2, actualResults[1].Record.Key);
        Assert.Equal($"data {TestRecordKey2}", actualResults[1].Record.Data);
        Assert.Equal(expectedScoreResult2, actualResults[1].Score);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanSearchManyRecordsAsync(bool useDefinition)
    {
        // Arrange
        var collection = new ConcurrentDictionary<object, object>();
        for (int i = 0; i < 1000; i++)
        {
            if (i <= 14)
            {
                collection.TryAdd(i, CreateModel(i, withVectors: true, new float[] { 1, 1, 1, 1 }));
            }
            else
            {
                collection.TryAdd(i, CreateModel(i, withVectors: true, new float[] { -1, -1, -1, -1 }));
            }
        }

        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = this.CreateRecordCollection<int>(useDefinition);

        // Act
        var actual = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new float[] { 1, 1, 1, 1 }),
            new() { IncludeVectors = true, Top = 10, Skip = 10, IncludeTotalCount = true },
            this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(1000, actual.TotalCount);

        // Assert that top was respected
        var actualResults = await actual.Results.ToListAsync();
        Assert.Equal(10, actualResults.Count);
        var actualIds = actualResults.Select(r => r.Record.Key).ToList();
        for (int i = 0; i < 10; i++)
        {
            // Assert that skip was respected
            Assert.Contains(i + 10, actualIds);
            if (i <= 4)
            {
                Assert.Equal(1, actualResults[i].Score);
            }
            else
            {
                Assert.Equal(-1, actualResults[i].Score);
            }
        }
    }

    [Theory]
    [InlineData(TestRecordKey1, TestRecordKey2)]
    [InlineData(TestRecordIntKey1, TestRecordIntKey2)]
    public async Task ItCanSearchUsingTheGenericDataModelAsync<TKey>(TKey testKey1, TKey testKey2)
        where TKey : notnull
    {
        // Arrange
        var record1 = new VectorStoreGenericDataModel<TKey>(testKey1)
        {
            Data = new Dictionary<string, object?>
            {
                ["Data"] = $"data {testKey1}",
                ["Tags"] = new List<string> { "default tag", "tag " + testKey1 }
            },
            Vectors = new Dictionary<string, object?>
            {
                ["Vector"] = new ReadOnlyMemory<float>([1, 1, 1, 1])
            }
        };
        var record2 = new VectorStoreGenericDataModel<TKey>(testKey2)
        {
            Data = new Dictionary<string, object?>
            {
                ["Data"] = $"data {testKey2}",
                ["Tags"] = new List<string> { "default tag", "tag " + testKey2 }
            },
            Vectors = new Dictionary<string, object?>
            {
                ["Vector"] = new ReadOnlyMemory<float>([-1, -1, -1, -1])
            }
        };

        var collection = new ConcurrentDictionary<object, object>();
        collection.TryAdd(testKey1, record1);
        collection.TryAdd(testKey2, record2);

        this._collectionStore.TryAdd(TestCollectionName, collection);

        var sut = new InMemoryVectorStoreRecordCollection<TKey, VectorStoreGenericDataModel<TKey>>(
            this._collectionStore,
            this._collectionStoreTypes,
            TestCollectionName,
            new()
            {
                VectorStoreRecordDefinition = this._singlePropsDefinition
            });

        // Act
        var actual = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>([1, 1, 1, 1]),
            new() { IncludeVectors = true, VectorProperty = r => r.Vectors["Vector"] },
            this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        var actualResults = await actual.Results.ToListAsync();
        Assert.Equal(2, actualResults.Count);
        Assert.Equal(testKey1, actualResults[0].Record.Key);
        Assert.Equal($"data {testKey1}", actualResults[0].Record.Data["Data"]);
        Assert.Equal(1, actualResults[0].Score);
        Assert.Equal(testKey2, actualResults[1].Record.Key);
        Assert.Equal($"data {testKey2}", actualResults[1].Record.Data["Data"]);
        Assert.Equal(-1, actualResults[1].Score);
    }

    private static SinglePropsModel<TKey> CreateModel<TKey>(TKey key, bool withVectors, float[]? vector = null)
    {
        return new SinglePropsModel<TKey>
        {
            Key = key,
            Data = "data " + key,
            Tags = new List<string> { "default tag", "tag " + key },
            Vector = vector ?? (withVectors ? new float[] { 1, 2, 3, 4 } : null),
            NotAnnotated = null,
        };
    }

    private InMemoryVectorStoreRecordCollection<TKey, SinglePropsModel<TKey>> CreateRecordCollection<TKey>(bool useDefinition)
        where TKey : notnull
    {
        return new InMemoryVectorStoreRecordCollection<TKey, SinglePropsModel<TKey>>(
            this._collectionStore,
            this._collectionStoreTypes,
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
            new VectorStoreRecordDataProperty("Tags", typeof(List<string>)) { IsFilterable = true },
            new VectorStoreRecordDataProperty("Data", typeof(string)) { IsFilterable = true },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>))
        ]
    };

    public sealed class SinglePropsModel<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; }

        [VectorStoreRecordData(IsFilterable = true)]
        public List<string> Tags { get; set; } = new List<string>();

        [VectorStoreRecordData(IsFilterable = true)]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
