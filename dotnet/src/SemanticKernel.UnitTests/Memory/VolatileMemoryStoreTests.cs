// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

public class VolatileMemoryStoreTests
{
    private readonly VolatileMemoryStore _db;

    public VolatileMemoryStoreTests()
    {
        this._db = new VolatileMemoryStore();
    }

    private int _collectionNum = 0;

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
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            records = records.Append(testRecord);
        }

        for (int i = numRecords / 2; i < numRecords; i++)
        {
            var testRecord = MemoryRecord.ReferenceRecord(
                externalId: "test" + i,
                sourceName: "sourceName" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            records = records.Append(testRecord);
        }

        return records;
    }

    [Fact]
    public void InitializeDbConnectionSucceeds()
    {
        // Assert
        Assert.NotNull(this._db);
    }

    [Fact]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await this._db.CreateCollectionAsync(collection);
        var collections = this._db.GetCollectionsAsync();

        // Assert
        Assert.NotEmpty(collections.ToEnumerable());
        Assert.True(await collections.ContainsAsync(collection));
    }

    [Fact]
    public async Task ItHandlesExceptionsWhenCreatingCollectionAsync()
    {
        // Arrange
        string? collection = null;

        // Assert
        await Assert.ThrowsAsync<ArgumentNullException>(async () => await this._db.CreateCollectionAsync(collection!));
    }

    [Fact]
    public async Task ItCannotInsertIntoNonExistentCollectionAsync()
    {
        // Arrange
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Assert
        await Assert.ThrowsAsync<MemoryException>(async () => await this._db.UpsertAsync(collection, testRecord));
    }

    [Fact]
    public async Task GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await this._db.CreateCollectionAsync(collection);
        var key = await this._db.UpsertAsync(collection, testRecord);
        var actualDefault = await this._db.GetAsync(collection, key);
        var actualWithEmbedding = await this._db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actualDefault);
        Assert.NotNull(actualWithEmbedding);
        Assert.Empty(actualDefault.Embedding.Vector);
        Assert.NotEmpty(actualWithEmbedding.Embedding.Vector);
        Assert.NotEqual(testRecord, actualDefault);
        Assert.Equal(testRecord, actualWithEmbedding);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithNoTimestampAsync()
    {
        // Arrange
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await this._db.CreateCollectionAsync(collection);
        var key = await this._db.UpsertAsync(collection, testRecord);
        var actual = await this._db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord, actual);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithTimestampAsync()
    {
        // Arrange
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: DateTimeOffset.UtcNow);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await this._db.CreateCollectionAsync(collection);
        var key = await this._db.UpsertAsync(collection, testRecord);
        var actual = await this._db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord, actual);
    }

    [Fact]
    public async Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        // Arrange
        string commonId = "test";
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: commonId,
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        MemoryRecord testRecord2 = MemoryRecord.LocalRecord(
            id: commonId,
            text: "text2",
            description: "description2",
            embedding: new Embedding<float>(new float[] { 1, 2, 4 }));
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await this._db.CreateCollectionAsync(collection);
        var key = await this._db.UpsertAsync(collection, testRecord);
        var key2 = await this._db.UpsertAsync(collection, testRecord2);
        var actual = await this._db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.NotEqual(testRecord, actual);
        Assert.Equal(key, key2);
        Assert.Equal(testRecord2, actual);
    }

    [Fact]
    public async Task ExistingRecordCanBeRemovedAsync()
    {
        // Arrange
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await this._db.CreateCollectionAsync(collection);
        var key = await this._db.UpsertAsync(collection, testRecord);
        await this._db.RemoveAsync(collection, key);
        var actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.Null(actual);
    }

    [Fact]
    public async Task RemovingNonExistingRecordDoesNothingAsync()
    {
        // Arrange
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await this._db.RemoveAsync(collection, "key");
        var actual = await this._db.GetAsync(collection, "key");

        // Assert
        Assert.Null(actual);
    }

    [Fact]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        string[] testCollections = { "test_collection5", "test_collection6", "test_collection7" };
        this._collectionNum += 3;
        await this._db.CreateCollectionAsync(testCollections[0]);
        await this._db.CreateCollectionAsync(testCollections[1]);
        await this._db.CreateCollectionAsync(testCollections[2]);

        // Act
        var collections = this._db.GetCollectionsAsync().ToEnumerable();

#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
        // Assert
        Assert.NotNull(collections);
        Assert.True(collections.Any(), "Collections is empty");
        Assert.Equal(3, collections.Count());
        Assert.True(collections.Contains(testCollections[0]),
            $"Collections does not contain the newly-created collection {testCollections[0]}");
        Assert.True(collections.Contains(testCollections[1]),
            $"Collections does not contain the newly-created collection {testCollections[1]}");
        Assert.True(collections.Contains(testCollections[2]),
            $"Collections does not contain the newly-created collection {testCollections[2]}");
    }
#pragma warning restore CA1851 // Possible multiple enumerations of 'IEnumerable' collection

    [Fact]
    public async Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await this._db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        // Act
        double threshold = -1;
        var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        for (int j = 0; j < topN - 1; j++)
        {
            int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await this._db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        // Act
        double threshold = 0.75;
        var topNResultDefault = await this._db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
        var topNResultWithEmbedding = await this._db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold, withEmbedding: true);

        // Assert
        Assert.NotNull(topNResultDefault);
        Assert.NotNull(topNResultWithEmbedding);
        Assert.Empty(topNResultDefault.Value.Item1.Embedding.Vector);
        Assert.NotEmpty(topNResultWithEmbedding.Value.Item1.Embedding.Vector);
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await this._db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await this._db.UpsertAsync(collection, testRecord);

        // Act
        double threshold = 0.75;
        var topNResult = await this._db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);

        // Assert
        Assert.NotNull(topNResult);
        Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
        Assert.True(topNResult.Value.Item2 >= threshold);
    }

    [Fact]
    public async Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await this._db.CreateCollectionAsync(collection);

        for (int i = 0; i < 10; i++)
        {
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await this._db.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();
        IEnumerable<string> topNKeys = topNResults.Select(x => x.Item1.Key).ToImmutableSortedSet();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        Assert.Equal(topN, topNKeys.Count());

        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task ItCanBatchUpsertRecordsAsync()
    {
        // Arrange
        int numRecords = 10;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await this._db.CreateCollectionAsync(collection);
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

        // Act
        var keys = this._db.UpsertBatchAsync(collection, records);
        var resultRecords = this._db.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.Equal(numRecords, keys.ToEnumerable().Count());
        Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
    }

    [Fact]
    public async Task ItCanBatchGetRecordsAsync()
    {
        // Arrange
        int numRecords = 10;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await this._db.CreateCollectionAsync(collection);
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        var keys = this._db.UpsertBatchAsync(collection, records);

        // Act
        var results = this._db.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.NotNull(results);
        Assert.Equal(numRecords, results.ToEnumerable().Count());
    }

    [Fact]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        int numRecords = 10;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await this._db.CreateCollectionAsync(collection);
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

        List<string> keys = new();
        await foreach (var key in this._db.UpsertBatchAsync(collection, records))
        {
            keys.Add(key);
        }

        // Act
        await this._db.RemoveBatchAsync(collection, keys);

        // Assert
        await foreach (var result in this._db.GetBatchAsync(collection, keys))
        {
            Assert.Null(result);
        }
    }

    [Fact]
    public async Task CollectionsCanBeDeletedAsync()
    {
        // Arrange
        var collections = this._db.GetCollectionsAsync().ToEnumerable();
#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
        int numCollections = collections.Count();
        Assert.True(numCollections == this._collectionNum);

        // Act
        foreach (var collection in collections)
        {
            await this._db.DeleteCollectionAsync(collection);
        }

        // Assert
        collections = this._db.GetCollectionsAsync().ToEnumerable();
        numCollections = collections.Count();
        Assert.True(numCollections == 0);
        this._collectionNum = 0;
    }
#pragma warning restore CA1851 // Possible multiple enumerations of 'IEnumerable' collection

    [Fact]
    public async Task ItThrowsWhenDeletingNonExistentCollectionAsync()
    {
        // Arrange
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await Assert.ThrowsAsync<MemoryException>(() => this._db.DeleteCollectionAsync(collection));
    }
}
