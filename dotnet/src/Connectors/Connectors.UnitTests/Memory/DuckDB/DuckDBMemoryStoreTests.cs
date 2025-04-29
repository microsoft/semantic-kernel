// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using DuckDB.NET.Data;
using Microsoft.SemanticKernel.Connectors.DuckDB;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.DuckDB;

/// <summary>
/// Unit tests of <see cref="DuckDBMemoryStore"/>.
/// </summary>
[Experimental("SKEXP0020")]
[Collection("Sequential")]
public class DuckDBMemoryStoreTests
{
    private int _collectionNum = 0;

    private string GetTestCollectionName([CallerMemberName] string testName = "")
    {
        return testName + this._collectionNum++;
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

    [Fact]
    public async Task InitializeDbConnectionSucceedsAsync()
    {
        using var db = await DuckDBMemoryStore.ConnectAsync();
        // Assert
        Assert.NotNull(db);
    }

    [Fact]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync();
        string collection = this.GetTestCollectionName();

        // Act
        await db.CreateCollectionAsync(collection);
        var collections = db.GetCollectionsAsync();

        // Assert
        Assert.NotEmpty(collections.ToEnumerable());
        Assert.True(await collections.ContainsAsync(collection));
    }

    [Fact]
    public async Task ItCanCheckIfCollectionExistsAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync();
        string collection = "my_collection+++";

        // Act
        await db.CreateCollectionAsync(collection);

        // Assert
        Assert.True(await db.DoesCollectionExistAsync("my_collection+++"));
        Assert.False(await db.DoesCollectionExistAsync("my_collection---"));
    }

    [Fact]
    public async Task CreatingDuplicateCollectionDoesNothingAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync();
        string collection = this.GetTestCollectionName();

        // Act
        await db.CreateCollectionAsync(collection);
        var collections = db.GetCollectionsAsync();
        await db.CreateCollectionAsync(collection);

        // Assert
        var collections2 = db.GetCollectionsAsync();
        Assert.Equal(await collections.CountAsync(), await collections.CountAsync());
    }

    [Fact]
    public async Task CollectionsCanBeDeletedAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync();
        string collection = this.GetTestCollectionName();

        await db.CreateCollectionAsync(collection);
        var collections = await db.GetCollectionsAsync().ToListAsync();
        Assert.True(collections.Count > 0);

        // Act
        foreach (var c in collections)
        {
            await db.DeleteCollectionAsync(c);
        }

        // Assert
        var collections2 = db.GetCollectionsAsync();
        Assert.Equal(0, await collections2.CountAsync());
    }

    [Fact]
    public async Task ItCanInsertIntoNonExistentCollectionAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);

        // Arrange
        var key = await db.UpsertAsync("random collection", testRecord);
        var actual = await db.GetAsync("random collection", key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.True(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact]
    public async Task ItCanNotInsertLargerVectorAsync()
    {
        // Arrange
        float[] embedding = new float[] { 1, 2, 3 };
        using var db = await DuckDBMemoryStore.ConnectAsync(embedding.Length - 1);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: embedding,
            key: null,
            timestamp: null);

        await Assert.ThrowsAsync<DuckDBException>(async () => await db.UpsertAsync("random collection", testRecord));
    }

    [Fact]
    public async Task ItCanNotInsertSmallerVectorAsync()
    {
        // Arrange
        float[] embedding = new float[] { 1, 2, 3 };
        using var db = await DuckDBMemoryStore.ConnectAsync(embedding.Length + 1);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: embedding,
            key: null,
            timestamp: null);

        await Assert.ThrowsAsync<DuckDBException>(async () => await db.UpsertAsync("random collection", testRecord));
    }

    [Fact]
    public async Task GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);
        string collection = this.GetTestCollectionName();

        // Act
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        var actualDefault = await db.GetAsync(collection, key);
        var actualWithEmbedding = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actualDefault);
        Assert.NotNull(actualWithEmbedding);
        Assert.True(actualDefault.Embedding.IsEmpty);
        Assert.Equal(actualWithEmbedding.Embedding.ToArray(), testRecord.Embedding.ToArray());
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithNoTimestampAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);
        string collection = this.GetTestCollectionName();

        // Act
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        var actual = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.True(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithTimestampAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: DateTimeOffset.UtcNow);
        string collection = this.GetTestCollectionName();

        // Act
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        var actual = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.True(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact]
    public async Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
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
        string collection = this.GetTestCollectionName();

        // Act
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        var key2 = await db.UpsertAsync(collection, testRecord2);
        var actual = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord2.Metadata.Id, actual.Key);
        Assert.False(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.True(testRecord2.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.NotEqual(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord2.Metadata.Description, actual.Metadata.Description);
    }

    [Fact]
    public async Task ExistingRecordCanBeRemovedAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 });
        string collection = this.GetTestCollectionName();

        // Act
        await db.CreateCollectionAsync(collection);
        var key = await db.UpsertAsync(collection, testRecord);
        await db.RemoveAsync(collection, key);
        var actual = await db.GetAsync(collection, key);

        // Assert
        Assert.Null(actual);
    }

    [Fact]
    public async Task RemovingNonExistingRecordDoesNothingAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync();
        string collection = "test_collection_for_record_deletion";

        // Act
        await db.CreateCollectionAsync(collection);
        await db.RemoveAsync(collection, "key");
        var actual = await db.GetAsync(collection, "key");

        // Assert
        Assert.Null(actual);
    }

    [Fact]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync();
        string[] testCollections = { "random_collection1", "random_collection2", "random_collection3" };

        await db.CreateCollectionAsync(testCollections[0]);
        await db.CreateCollectionAsync(testCollections[1]);
        await db.CreateCollectionAsync(testCollections[2]);

        // Act
        var collections = await db.GetCollectionsAsync().ToListAsync();

        // Assert
        foreach (var collection in testCollections)
        {
            Assert.True(await db.DoesCollectionExistAsync(collection));
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
    }

    [Fact]
    public async Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        int topN = 4;
        string collection = this.GetTestCollectionName();

        await db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 1, 1 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -1, -1 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 2, 3 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -2, -3 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, -1, -2 });
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
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        string collection = this.GetTestCollectionName();

        await db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 1, 1 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -1, -1 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 2, 3 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -2, -3 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, -1, -2 });
        _ = await db.UpsertAsync(collection, testRecord);

        // Act
        double threshold = 0.75;
        var topNResultDefault = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
        var topNResultWithEmbedding = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold, withEmbedding: true);

        // Assert
        Assert.NotNull(topNResultDefault);
        Assert.NotNull(topNResultWithEmbedding);
        Assert.True(topNResultDefault.Value.Item1.Embedding.IsEmpty);
        Assert.False(topNResultWithEmbedding.Value.Item1.Embedding.IsEmpty);
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        string collection = this.GetTestCollectionName();

        await db.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 1, 1 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -1, -1 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, 2, 3 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { -1, -2, -3 });
        _ = await db.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new float[] { 1, -1, -2 });
        _ = await db.UpsertAsync(collection, testRecord);

        // Act
        double threshold = 0.75;
        var topNResult = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);

        // Assert
        Assert.NotNull(topNResult);
        Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
        Assert.True(topNResult.Value.Item2 >= threshold);
    }

    [Fact]
    public async Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        int topN = 4;
        string collection = this.GetTestCollectionName();

        await db.CreateCollectionAsync(collection);

        for (int i = 0; i < 10; i++)
        {
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new float[] { 1, 1, 1 });
            _ = await db.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResults = db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();
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
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        int numRecords = 10;
        string collection = this.GetTestCollectionName();

        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

        // Act
        await db.CreateCollectionAsync(collection);
        var keys = db.UpsertBatchAsync(collection, records);
        var resultRecords = db.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.Equal(numRecords, keys.ToEnumerable().Count());
        Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
    }

    [Fact]
    public async Task ItCanBatchGetRecordsAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        int numRecords = 10;
        string collection = this.GetTestCollectionName();

        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        var keys = db.UpsertBatchAsync(collection, records);

        // Act
        await db.CreateCollectionAsync(collection);
        var results = db.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.NotNull(results);
        Assert.Equal(numRecords, results.ToEnumerable().Count());
    }

    [Fact]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        int numRecords = 10;
        string collection = this.GetTestCollectionName();

        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        await db.CreateCollectionAsync(collection);

        List<string> keys = [];

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
    }

    [Fact]
    public async Task DeletingNonExistentCollectionDoesNothingAsync()
    {
        // Arrange
        using var db = await DuckDBMemoryStore.ConnectAsync(3);
        string collection = this.GetTestCollectionName();

        // Act
        await db.DeleteCollectionAsync(collection);
    }
}
