// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using System.Threading.Tasks;
using Cloud.Unum.USearch;
using Microsoft.SemanticKernel.Connectors.Memory.USearch;
using Microsoft.SemanticKernel.Memory;
using Xunit;
namespace SemanticKernel.Connectors.UnitTests.Memory.USearch;

public class USearchMemoryStoreTests
{
    private const string CollectionName = "fake-collection-name";

    public USearchMemoryStoreTests()
    {
    }

    [Fact]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);

        // Act
        await store.CreateCollectionAsync(CollectionName);
        var collections = store.GetCollectionsAsync();

        // Assert
        Assert.NotEmpty(collections.ToEnumerable());
        Assert.True(await collections.ContainsAsync(CollectionName));

        store.Dispose();
    }

    [Fact]
    public async Task ItCanCheckIfCollectionExistsAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);

        // Act
        await store.CreateCollectionAsync(CollectionName);

        // Assert
        Assert.True(await store.DoesCollectionExistAsync(CollectionName));
        Assert.False(await store.DoesCollectionExistAsync(CollectionName + "_2"));

        store.Dispose();
    }

    [Fact]
    public async Task CreatingDuplicateCollectionDoesNothingAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);

        // Act
        await store.CreateCollectionAsync(CollectionName);
        var collections = store.GetCollectionsAsync();
        await store.CreateCollectionAsync(CollectionName);
        var collections2 = store.GetCollectionsAsync();

        // Assert
        Assert.Equal(await collections.CountAsync(), await collections.CountAsync());

        store.Dispose();
    }

    [Fact]
    public async Task ItCanDeleteCollectionsAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        await store.CreateCollectionAsync(CollectionName);

        // Act
        var collections = await store.GetCollectionsAsync().ToListAsync();
        foreach (var c in collections)
        {
            await store.DeleteCollectionAsync(c);
        }
        var collections2 = store.GetCollectionsAsync();

        // Assert
        Assert.True(collections.Count > 0);
        Assert.True(await collections2.CountAsync() == 0);

        store.Dispose();
    }

    [Fact]
    public async Task ItCanInsertIntoCollectionAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);
        await store.CreateCollectionAsync(CollectionName);

        // Arrange
        var key = await store.UpsertAsync(CollectionName, testRecord);
        var actual = await store.GetAsync(CollectionName, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.True(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);

        store.Dispose();
    }

    [Fact]
    public async Task GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);
        await store.CreateCollectionAsync(CollectionName);
        var key = await store.UpsertAsync(CollectionName, testRecord);

        // Act
        var actualDefault = await store.GetAsync(CollectionName, key);
        var actualWithEmbedding = await store.GetAsync(CollectionName, key, true);

        // Assert
        Assert.NotNull(actualDefault);
        Assert.NotNull(actualWithEmbedding);
        Assert.True(actualDefault.Embedding.IsEmpty);
        Assert.False(actualWithEmbedding.Embedding.IsEmpty);

        store.Dispose();
    }

    [Fact]
    public async Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        string commonId = "test";
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: commonId,
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 });
        MemoryRecord testRecord2 = MemoryRecord.LocalRecord(
            id: commonId,
            text: "text2",
            description: "description2",
            embedding: new float[] { 1, 2, 4 });
        await store.CreateCollectionAsync(CollectionName);

        // Act
        var key = await store.UpsertAsync(CollectionName, testRecord);
        var key2 = await store.UpsertAsync(CollectionName, testRecord2);
        var actual = await store.GetAsync(CollectionName, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord2.Metadata.Id, actual.Key);
        Assert.False(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.True(testRecord2.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.NotEqual(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord2.Metadata.Description, actual.Metadata.Description);

        store.Dispose();
    }

    [Fact]
    public async Task ItCanRemoveExistingRecordAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 });
        await store.CreateCollectionAsync(CollectionName);
        var key = await store.UpsertAsync(CollectionName, testRecord);

        // Act
        await store.RemoveAsync(CollectionName, key);
        var actual = await store.GetAsync(CollectionName, key);

        // Assert
        Assert.Null(actual);

        store.Dispose();
    }

    [Fact]
    public async Task RemovingOrGettingNonExistingRecordDoesNothingAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        await store.CreateCollectionAsync(CollectionName);

        // Act
        await store.RemoveAsync(CollectionName, "key");
        var actual = await store.GetAsync(CollectionName, "key");

        // Assert
        Assert.Null(actual);

        store.Dispose();
    }

    [Fact]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        string[] testCollections = { "random_collection1", "random_collection2", "random_collection3" };
        await store.CreateCollectionAsync(testCollections[0]);
        await store.CreateCollectionAsync(testCollections[1]);
        await store.CreateCollectionAsync(testCollections[2]);

        // Act
        var collections = await store.GetCollectionsAsync().ToListAsync();

        // Assert
        foreach (var collection in testCollections)
        {
            Assert.True(await store.DoesCollectionExistAsync(collection));
        }

        Assert.NotNull(collections);
        Assert.NotEmpty(collections);
        Assert.Equal(testCollections.Length, collections.Count);
        Assert.True(collections.Contains(testCollections[0]),
            $"Collections does not contain the newly-created collection {testCollections[0]}");
        Assert.True(collections.Contains(testCollections[1]),
            $"Collections does not contain the newly-created collection {testCollections[1]}");
        Assert.True(collections.Contains(testCollections[2]),
            $"Collections does not contain the newly-created collection {testCollections[2]}");

        store.Dispose();
    }

    [Fact]
    public async Task ItCanBatchUpsertRecordsAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        int numRecords = 10;
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        await store.CreateCollectionAsync(CollectionName);

        // Act
        var keys = store.UpsertBatchAsync(CollectionName, records);
        var resultRecords = store.GetBatchAsync(CollectionName, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.NotNull(resultRecords);
        Assert.Equal(numRecords, keys.ToEnumerable().Count());
        Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());

        store.Dispose();
    }

    [Fact]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Ip, 3);
        int numRecords = 10;
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        List<string> keys = new();
        await store.CreateCollectionAsync(CollectionName);
        await foreach (var key in store.UpsertBatchAsync(CollectionName, records))
        {
            keys.Add(key);
        }

        // Act
        await store.RemoveBatchAsync(CollectionName, keys);

        // Assert
        await foreach (var result in store.GetBatchAsync(CollectionName, keys))
        {
            Assert.Null(result);
        }

        store.Dispose();
    }

    //[Fact(Skip = "Issue with negative distances in USearch")]
    [Fact]
    public async Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Cos, 3);

        var compareEmbedding = new float[] { 1, 1, 1 };
        int topN = 4;
        await store.CreateCollectionAsync(CollectionName);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 1, 1 });
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -1, -1 });
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 2, 3 });
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -2, -3 });
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, -1, -2 });
        _ = store.UpsertAsync(CollectionName, testRecord);

        // Act
        double threshold = 0;
        var topNResults = store.GetNearestMatchesAsync(CollectionName, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        for (int j = 0; j < topN - 1; j++)
        {
            int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
            Assert.True(compare >= 0);
        }

        store.Dispose();
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Cos, 3);

        var compareEmbedding = new float[] { 1, 1, 1 };
        await store.CreateCollectionAsync(CollectionName);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 1, 1 });
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new ReadOnlyMemory<float>(new float[] { -1, -1, -1 }));
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 2, 3 });
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new ReadOnlyMemory<float>(new float[] { -1, -2, -3 }));
        _ = store.UpsertAsync(CollectionName, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new ReadOnlyMemory<float>(new float[] { 1, -1, -2 }));
        _ = store.UpsertAsync(CollectionName, testRecord);

        // Act
        double threshold = 0.75;
        var topNResult = await store.GetNearestMatchAsync(CollectionName, compareEmbedding, minRelevanceScore: threshold);

        // Assert
        Assert.NotNull(topNResult);
        Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
        Assert.True(topNResult.Value.Item2 >= threshold);

        store.Dispose();
    }

    [Fact]
    public async Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        var store = new USearchMemoryStore(MetricKind.Cos, 3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        int topN = 4;
        await store.CreateCollectionAsync(CollectionName);

        for (int i = 0; i < 10; i++)
        {
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new float[] { 1, 1, 1 });
            _ = store.UpsertAsync(CollectionName, testRecord);
        }

        // Act
        var topNResults = store.GetNearestMatchesAsync(CollectionName, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();
        IEnumerable<string> topNKeys = topNResults.Select(x => x.Item1.Key).ToImmutableSortedSet();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        Assert.Equal(topN, topNKeys.Count());

        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }

        store.Dispose();
    }

    private IEnumerable<MemoryRecord> CreateBatchRecords(int numRecords)
    {
        Assert.True(numRecords % 2 == 0, "Number of records must be even");
        Assert.True(numRecords > 0, "Number of records must be greater than 0");

        IEnumerable<MemoryRecord> records = new List<MemoryRecord>(numRecords);
        for (int i = 0; i < numRecords / 2; i++)
        {
            var testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new float[] { 1, 1, 1 });
            records = records.Append(testRecord);
        }

        for (int i = numRecords / 2; i < numRecords; i++)
        {
            var testRecord = MemoryRecord.ReferenceRecord(
                externalId: "test" + i,
                sourceName: "sourceName" + i,
                description: "description" + i,
                embedding: new float[] { 1, 2, 3 });
            records = records.Append(testRecord);
        }

        return records;
    }
}
