// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

/// <summary>
/// Integration tests of <see cref="MongoDBMemoryStore"/>.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class MongoDBMemoryStoreTests(MongoDBMemoryStoreTestsFixture fixture) : IClassFixture<MongoDBMemoryStoreTestsFixture>
{
    // If null, all tests will be enabled
    private const string? SkipReason = "MongoDB Atlas cluster is required";

    private readonly MongoDBMemoryStoreTestsFixture _fixture = fixture;

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        var collectionNames = memoryStore.GetCollectionsAsync();

        // Assert
        Assert.True(await collectionNames.ContainsAsync(collectionName));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCheckIfCollectionExistsAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);

        // Assert
        Assert.True(await memoryStore.DoesCollectionExistAsync(collectionName));
        Assert.False(await memoryStore.DoesCollectionExistAsync($"{collectionName}_1"));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionsAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        var collectionExistsAfterCreation = await memoryStore.DoesCollectionExistAsync(collectionName);
        await memoryStore.DeleteCollectionAsync(collectionName);

        // Assert
        Assert.True(collectionExistsAfterCreation);
        Assert.False(await memoryStore.DoesCollectionExistAsync(collectionName));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanTryDeleteNonExistingCollectionAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        // Act
        await memoryStore.DeleteCollectionAsync(collectionName);

        // Assert
        Assert.False(await memoryStore.DoesCollectionExistAsync(collectionName));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanBatchGetAsync()
    {
        // Arrange
        const string Id = "test";
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        var testRecord = DataHelper.CreateRecord(Id);

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        var upsertedId = await memoryStore.UpsertAsync(collectionName, testRecord);

        var actualNoEmbedding = await memoryStore.GetAsync(collectionName, upsertedId);
        var actualWithEmbedding = await memoryStore.GetAsync(collectionName, upsertedId, true);

        // Assert
        Assert.NotNull(actualNoEmbedding);
        Assert.NotNull(actualWithEmbedding);
        AssertMemoryRecordEqualWithoutEmbedding(testRecord, actualNoEmbedding);
        AssertMemoryRecordEqual(testRecord, actualWithEmbedding);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetEmptyEmbeddingAsync()
    {
        // Arrange
        const string Id = "test";
        const string CollectionName = "test_collection";
        var memoryStore = this._fixture.MemoryStore;

        var testRecord = DataHelper.CreateRecord(Id);

        // Act
        await memoryStore.CreateCollectionAsync(CollectionName);
        var upsertedId = await memoryStore.UpsertAsync(CollectionName, testRecord);

        var actualNoEmbedding = await memoryStore.GetAsync(CollectionName, upsertedId);
        var actualWithEmbedding = await memoryStore.GetAsync(CollectionName, upsertedId, true);

        // Assert
        Assert.NotNull(actualNoEmbedding);
        Assert.NotNull(actualWithEmbedding);
        AssertMemoryRecordEqualWithoutEmbedding(testRecord, actualNoEmbedding);
        AssertMemoryRecordEqual(testRecord, actualWithEmbedding);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanBatchUpsertRecordsAsync(bool withEmbeddings)
    {
        // Arrange
        const int Count = 10;
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;
        var records = DataHelper.CreateBatchRecords(Count);

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        var keys = await memoryStore.UpsertBatchAsync(collectionName, records).ToListAsync();
        var actualRecords = await memoryStore.GetBatchAsync(collectionName, keys, withEmbeddings: withEmbeddings).ToListAsync();

        // Assert
        Assert.NotNull(keys);
        Assert.NotNull(actualRecords);
        Assert.Equal(Count, keys.Count);
        Assert.Equal(Count, actualRecords.Count);

        var actualRecordsOrdered = actualRecords.OrderBy(r => r.Key).ToArray();
        for (int i = 0; i < Count; i++)
        {
            AssertMemoryRecordEqual(records[i], actualRecordsOrdered[i], assertEmbeddingEqual: withEmbeddings);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertDifferentMemoryRecordsWithSameKeyAsync()
    {
        // Arrange
        const string Id = "test";
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        var testRecord1 = MemoryRecord.LocalRecord(
            id: Id,
            text: "text1",
            description: "description",
            embedding: new float[] { 1, 2, 3 });
        var testRecord2 = MemoryRecord.LocalRecord(
            id: Id,
            text: "text2",
            description: "description new",
            embedding: new float[] { 1, 2, 4 });

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        var upsertedId1 = await memoryStore.UpsertAsync(collectionName, testRecord1);
        var actual1 = await memoryStore.GetAsync(collectionName, Id, true);

        var upsertedId2 = await memoryStore.UpsertAsync(collectionName, testRecord2);
        var actual2 = await memoryStore.GetAsync(collectionName, Id, true);

        // Assert
        Assert.NotNull(actual1);
        Assert.NotNull(actual2);
        AssertMemoryRecordEqual(testRecord1, actual1);
        AssertMemoryRecordEqual(testRecord2, actual2);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveRecordAsync()
    {
        // Arrange
        const string Id = "test";
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        var testRecord = DataHelper.CreateRecord(Id);

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        await memoryStore.UpsertAsync(collectionName, testRecord);
        await memoryStore.RemoveAsync(collectionName, Id);

        // Assert
        var actual = await memoryStore.GetAsync(collectionName, Id);
        Assert.Null(actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanTryRemovingNonExistingRecordAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        await memoryStore.RemoveAsync(collectionName, "key");

        var actual = await memoryStore.GetAsync(collectionName, "key");

        // Assert
        Assert.Null(actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;
        var testRecords = DataHelper.CreateBatchRecords(10);

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        var ids = await memoryStore.UpsertBatchAsync(collectionName, testRecords).ToListAsync();
        await memoryStore.RemoveBatchAsync(collectionName, ids);

        // Assert
        var actual = await memoryStore.GetBatchAsync(collectionName, ids).ToListAsync();
        Assert.Empty(actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanTryBatchRemovingNonExistingRecordsAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;
        string[] ids = ["a", "b", "c"];

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        await memoryStore.RemoveBatchAsync(collectionName, ids);

        // Assert
        var actual = await memoryStore.GetBatchAsync(collectionName, ids).ToListAsync();
        Assert.Empty(actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanTryBatchRemovingMixedExistingAndNonExistingRecordsAsync()
    {
        // Arrange
        var collectionName = GetRandomName();
        var memoryStore = this._fixture.MemoryStore;
        var testRecords = DataHelper.CreateBatchRecords(10);
        var ids = testRecords.Select(t => t.Metadata.Id).Concat(["a", "b", "c"]).ToArray();

        // Act
        await memoryStore.CreateCollectionAsync(collectionName);
        await memoryStore.RemoveBatchAsync(collectionName, ids);

        // Assert
        var actual = await memoryStore.GetBatchAsync(collectionName, ids).ToListAsync();
        Assert.Empty(actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        var memoryStore = this._fixture.ListCollectionsMemoryStore;
        string[] testCollections = ["collection1", "collection2", "collection3"];
        foreach (var collection in testCollections)
        {
            await memoryStore.CreateCollectionAsync(collection);
        }

        // Act
        var actualCollections = await memoryStore.GetCollectionsAsync().ToListAsync();
        actualCollections?.Sort();

        // Assert
        foreach (var collection in testCollections)
        {
            Assert.True(await memoryStore.DoesCollectionExistAsync(collection));
        }

        Assert.NotNull(actualCollections);
        Assert.True(testCollections.SequenceEqual(actualCollections));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanGetNearestMatchAsync(bool withEmbedding)
    {
        // Arrange
        var collectionName = this._fixture.VectorSearchCollectionName;
        var memoryStore = this._fixture.VectorSearchMemoryStore;
        var searchEmbedding = DataHelper.VectorSearchTestEmbedding;
        var nearestMatchExpected = DataHelper.VectorSearchExpectedResults[0];

        // Act
        var nearestMatch = await memoryStore.GetNearestMatchAsync(collectionName, searchEmbedding, withEmbedding: withEmbedding);

        // Assert
        Assert.NotNull(nearestMatch);

        var actual = nearestMatch.Value.Item1;
        Assert.NotNull(actual);
        Assert.InRange(nearestMatch.Value.Item2, 0.9999, 1);
        AssertMemoryRecordEqual(nearestMatchExpected, actual, assertEmbeddingEqual: withEmbedding);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(1, false)]
    [InlineData(1, true)]
    [InlineData(5, false)]
    [InlineData(8, false)]
    public async Task ItCanGetNearestMatchesAsync(int limit, bool withEmbeddings)
    {
        // Arrange
        var collectionName = this._fixture.VectorSearchCollectionName;
        var memoryStore = this._fixture.VectorSearchMemoryStore;
        var searchEmbedding = DataHelper.VectorSearchTestEmbedding;
        var nearestMatchesExpected = DataHelper.VectorSearchExpectedResults;

        // Act
        var nearestMatchesActual = await memoryStore.GetNearestMatchesAsync(
            collectionName,
            searchEmbedding,
            limit,
            withEmbeddings: withEmbeddings)
            .ToListAsync();

        // Assert
        Assert.NotNull(nearestMatchesActual);
        Assert.Equal(nearestMatchesActual.Count, limit);

        for (int i = 0; i < limit; i++)
        {
            AssertMemoryRecordEqual(nearestMatchesExpected[i], nearestMatchesActual[i].Item1, withEmbeddings);
        }
    }

    [Theory(Skip = SkipReason)]
    [InlineData(0.999, 1, false)]
    [InlineData(0.847, 5, false)]
    [InlineData(0.847, 5, true)]
    [InlineData(0.111, 8, false)]
    public async Task ItCanGetNearestMatchesFilteredByMinScoreAsync(double minScore, int expectedCount, bool withEmbeddings)
    {
        // Arrange
        var collectionName = this._fixture.VectorSearchCollectionName;
        var memoryStore = this._fixture.VectorSearchMemoryStore;
        var searchEmbedding = DataHelper.VectorSearchTestEmbedding;
        var nearestMatchesExpected = DataHelper.VectorSearchExpectedResults;

        // Act
        var nearestMatchesActual = await memoryStore.GetNearestMatchesAsync(
            collectionName,
            searchEmbedding,
            100,
            minScore,
            withEmbeddings: withEmbeddings)
            .ToListAsync();

        // Assert
        Assert.NotNull(nearestMatchesActual);
        Assert.Equal(nearestMatchesActual.Count, expectedCount);

        for (int i = 0; i < expectedCount; i++)
        {
            AssertMemoryRecordEqual(nearestMatchesExpected[i], nearestMatchesActual[i].Item1, withEmbeddings);
        }
    }

    #region private ================================================================================

    private static void AssertMemoryRecordEqualWithoutEmbedding(MemoryRecord expectedRecord, MemoryRecord actualRecord) =>
        AssertMemoryRecordEqual(expectedRecord, actualRecord, false);

    private static void AssertMemoryRecordEqual(MemoryRecord expectedRecord, MemoryRecord actualRecord, bool assertEmbeddingEqual = true)
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Timestamp, actualRecord.Timestamp);
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(expectedRecord.Metadata.AdditionalMetadata, actualRecord.Metadata.AdditionalMetadata);
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(expectedRecord.Metadata.ExternalSourceName, actualRecord.Metadata.ExternalSourceName);

        if (assertEmbeddingEqual)
        {
            Assert.True(expectedRecord.Embedding.Span.SequenceEqual(actualRecord.Embedding.Span));
        }
        else
        {
            Assert.True(actualRecord.Embedding.Span.IsEmpty);
        }
    }

    private static string GetRandomName() => $"test_{Guid.NewGuid():N}";

    #endregion
}
