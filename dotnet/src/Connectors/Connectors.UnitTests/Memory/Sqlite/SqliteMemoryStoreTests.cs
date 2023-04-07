// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Sqlite;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Sqlite;

/// <summary>
/// Unit tests of <see cref="SqliteMemoryStore"/>.
/// </summary>
public class SqliteMemoryStoreTests
{
    private const string DatabaseFile = "SqliteMemoryStoreTests.db";

    public SqliteMemoryStoreTests()
    {
        File.Delete(DatabaseFile);
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
    public async Task InitializeDbConnectionSucceedsAsync()
    {
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        // Assert
        Assert.NotNull(db);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);
        var collections = db.GetCollectionsAsync();

        // Assert
        Assert.NotEmpty(collections.ToEnumerable());
        Assert.True(await collections.ContainsAsync(collection));
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanCheckIfCollectionExistsAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        string collection = "my_collection";
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);

        // Assert
        Assert.True(await db.DoesCollectionExistAsync("my_collection"));
        Assert.False(await db.DoesCollectionExistAsync("my_collection2"));
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task CreatingDuplicateCollectionDoesNothingAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);
        var collections = db.GetCollectionsAsync();
        await db.CreateCollectionAsync(collection);

        // Assert
        var collections2 = db.GetCollectionsAsync();
        Assert.Equal(await collections.CountAsync(), await collections.CountAsync());
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task CollectionsCanBeDeletedAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        var collections = await db.GetCollectionsAsync().ToListAsync();
        int numCollections = collections.Count;
        Assert.True(numCollections > 0);

        // Act
        foreach (var collection in collections)
        {
            await db.DeleteCollectionAsync(collection);
        }

        // Assert
        var collections2 = db.GetCollectionsAsync();
        numCollections = await collections2.CountAsync();
        Assert.True(numCollections == 0);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanInsertIntoNonExistentCollectionAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);

        // Arrange
        var key = await db.UpsertAsync("random collection", testRecord);
        var actual = await db.GetAsync("random collection", key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithNoTimestampAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
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
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        var actual = await db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithTimestampAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
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
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        var actual = await db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
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
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        var key2 = await db.UpsertAsync(collection, testRecord2);
        var actual = await db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord2.Metadata.Id, actual.Key);
        Assert.NotEqual(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord2.Embedding.Vector, actual.Embedding.Vector);
        Assert.NotEqual(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord2.Metadata.Description, actual.Metadata.Description);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ExistingRecordCanBeRemovedAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        await db.RemoveAsync(collection, key);
        var actual = await db.GetAsync(collection, key);

        // Assert
        Assert.Null(actual);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task RemovingNonExistingRecordDoesNothingAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);
        await db.RemoveAsync(collection, "key");
        var actual = await db.GetAsync(collection, "key");

        // Assert
        Assert.Null(actual);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        string[] testCollections = { "random_collection1", "random_collection2", "random_collection3" };
        this._collectionNum += 3;
        await db.CreateCollectionAsync(testCollections[0]);
        await db.CreateCollectionAsync(testCollections[1]);
        await db.CreateCollectionAsync(testCollections[2]);

        // Act
        var collections = await db.GetCollectionsAsync().ToListAsync();

#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
        // Assert
        foreach (var collection in testCollections)
        {
            Assert.True(await db.DoesCollectionExistAsync(collection));
        }

        Assert.NotNull(collections);
        Assert.NotEmpty(collections);
        Assert.True(collections.Count > 3);
        Assert.True(collections.Contains(testCollections[0]),
            $"Collections does not contain the newly-created collection {testCollections[0]}");
        Assert.True(collections.Contains(testCollections[1]),
            $"Collections does not contain the newly-created collection {testCollections[1]}");
        Assert.True(collections.Contains(testCollections[2]),
            $"Collections does not contain the newly-created collection {testCollections[2]}");
        db.Dispose();
        File.Delete(DatabaseFile);
    }
#pragma warning restore CA1851 // Possible multiple enumerations of 'IEnumerable' collection

    [Fact]
    public async Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await db.UpsertAsync(collection, testRecord);

        // Act
        double threshold = -1;
        var topNResults = db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        for (int j = 0; j < topN - 1; j++)
        {
            int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
            Assert.True(compare >= 0);
        }

        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await db.UpsertAsync(collection, testRecord);

        // Act
        double threshold = 0.75;
        var topNResult = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);

        // Assert
        Assert.NotNull(topNResult);
        Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
        Assert.True(topNResult.Value.Item2 >= threshold);
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        await db.CreateCollectionAsync(collection);

        for (int i = 0; i < 10; i++)
        {
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await db.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResults = db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();
        IEnumerable<string> topNKeys = topNResults.Select(x => x.Item1.Key).ToImmutableSortedSet();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        Assert.Equal(topNKeys.Count(), topNResults.Length);

        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }

        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanBatchUpsertRecordsAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        int numRecords = 10;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

        // Act
        await db.CreateCollectionAsync(collection);
        var keys = db.UpsertBatchAsync(collection, records);
        var resultRecords = db.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.Equal(numRecords, keys.ToEnumerable().Count());
        Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanBatchGetRecordsAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        int numRecords = 10;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        var keys = db.UpsertBatchAsync(collection, records);

        // Act
        await db.CreateCollectionAsync(collection);
        var results = db.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.NotNull(results);
        Assert.Equal(numRecords, results.ToEnumerable().Count());
        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        int numRecords = 10;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        await db.CreateCollectionAsync(collection);

        List<string> keys = new();

        // Act
        await foreach (var key in db.UpsertBatchAsync(collection, records))
        {
            keys.Add(key);
        }

        await db.RemoveBatchAsync(collection, keys);

        // Assert
        await foreach (var result in db.GetBatchAsync(collection, keys))
        {
            Assert.Null(result);
        }

        db.Dispose();
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task DeletingNonExistentCollectionDoesNothingAsync()
    {
        // Arrange
        SqliteMemoryStore db = await SqliteMemoryStore.ConnectAsync(DatabaseFile);
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.DeleteCollectionAsync(collection);
        db.Dispose();
        File.Delete(DatabaseFile);
    }
}
