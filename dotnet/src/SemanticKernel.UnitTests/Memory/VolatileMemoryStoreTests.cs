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
    
    private IEnumerable<MemoryRecord> CreateBatchLocalRecords(int numRecords)
    {
        IEnumerable<MemoryRecord> records = new List<MemoryRecord>(numRecords);
        for (int i = 0; i < numRecords; i++)
        {
            var testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            records = records.Append(testRecord);
        }

        return records;
    }

    private IEnumerable<MemoryRecord> CreateBatchReferenceRecords(int numRecords)
    {
        IEnumerable<MemoryRecord> records = new List<MemoryRecord>(numRecords);
        for (int i = 0; i < numRecords; i++)
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
    public async Task UpsertAndRetrieveNoTimestampSucceedsAsync()
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
        var key = await this._db.UpsertAsync(collection, testRecord);
        var actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord, actual);
    }

    [Fact]
    public async Task UpsertAndRetrieveWithTimestampSucceedsAsync()
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
        var key = await this._db.UpsertAsync(collection, testRecord);
        var actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord, actual);
    }
    
    [Fact]
    public async Task ListAllDatabaseCollectionsSucceedsAsync()
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
    public async Task GetNearestAsyncReturnsExpectedNoMinScoreAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
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
        var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: -1).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        for (int j = 0; j < topN - 1; j++)
        {
            int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task GetNearestAsyncReturnsExpectedWithMinScoreAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
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
        var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();

        // Assert
        for (int j = 0; j < topNResults.Length; j++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task GetNearestAsyncDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

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
        Assert.Equal(topNKeys.Count(), topNResults.Length);

        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public Task CanBatchUpsertRecordsAsync()
    {
        // Arrange
        int numRecords = 5;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        IEnumerable<MemoryRecord> records = this.CreateBatchLocalRecords(numRecords);

        // Act
        var keys = this._db.UpsertBatchAsync(collection, records).ToEnumerable();
        var resultRecords = this._db.GetBatchAsync(collection, keys).ToEnumerable();

        // Assert
        Assert.Equal(numRecords, keys.Count());
        Assert.Equal(numRecords, resultRecords.Count());
    }

    [Fact]
    public Task CanBatchGetRecordsAsync()
    {
        // Arrange
        int numRecords = 5;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        IEnumerable<MemoryRecord> records = this.CreateBatchReferenceRecords(numRecords);
        var keys = this._db.UpsertBatchAsync(collection, records).ToEnumerable();

        // Act
        var results = this._db.GetBatchAsync(collection, keys).ToEnumerable();

        // Assert
        Assert.Equal(numRecords, results.Count());
    }

    [Fact]
    public async Task CanBatchRemoveRecordsAsync()
    {
        // Arrange
        int numRecords = 5;
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        IEnumerable<MemoryRecord> records = this.CreateBatchReferenceRecords(numRecords);
        var keys = this._db.UpsertBatchAsync(collection, records).ToEnumerable();

        // Act
        await this._db.RemoveBatchAsync(collection, keys);
        var results = this._db.GetBatchAsync(collection, keys).ToEnumerable();

        // Assert
        Assert.Empty(results);
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
}
