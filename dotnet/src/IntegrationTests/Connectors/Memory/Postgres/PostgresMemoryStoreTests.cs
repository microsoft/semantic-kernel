// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Postgres;
using Microsoft.SemanticKernel.Memory;
using Npgsql;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Postgres;

/// <summary>
/// Integration tests of <see cref="PostgresMemoryStore"/>.
/// </summary>
public class PostgresMemoryStoreTests : IDisposable
{
    // Set null enable tests
    private const string SkipOrNot = "Required posgres with pgvector extension";

    private const string ConnectionString = "Host=localhost;Database={0};User Id=postgres";
    private readonly string _databaseName;

    private bool _disposedValue = false;

    public PostgresMemoryStoreTests()
    {
#pragma warning disable CA5394
        this._databaseName = $"sk_pgvector_dotnet_it_{Random.Shared.Next(0, 1000)}";
#pragma warning restore CA5394
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                using NpgsqlConnection conn = new(string.Format(CultureInfo.CurrentCulture, ConnectionString, "postgres"));
                conn.Open();
#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
                using NpgsqlCommand command = new($"DROP DATABASE IF EXISTS \"{this._databaseName}\"", conn);
#pragma warning restore CA2100 // Review SQL queries for security vulnerabilities
                command.ExecuteNonQuery();
            }

            this._disposedValue = true;
        }
    }

    private int _collectionNum = 0;

    private async Task TryCreateDatabaseAsync()
    {
        using NpgsqlConnection conn = new(string.Format(CultureInfo.CurrentCulture, ConnectionString, "postgres"));
        await conn.OpenAsync();
        using NpgsqlCommand checkCmd = new("SELECT COUNT(*) FROM pg_database WHERE datname = @databaseName", conn);
        checkCmd.Parameters.AddWithValue("@databaseName", this._databaseName);

        var count = (long?)await checkCmd.ExecuteScalarAsync();
        if (count == 0)
        {
#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
            using var createCmd = new NpgsqlCommand($"CREATE DATABASE \"{this._databaseName}\"", conn);
#pragma warning restore CA2100 // Review SQL queries for security vulnerabilities
            await createCmd.ExecuteNonQueryAsync();
        }
    }

    private async Task<PostgresMemoryStore> CreateMemoryStoreAsync()
    {
        await this.TryCreateDatabaseAsync();
        return await PostgresMemoryStore.ConnectAsync(string.Format(CultureInfo.CurrentCulture, ConnectionString, this._databaseName), vectorSize: 3);
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

    [Fact(Skip = SkipOrNot)]
    public async Task InitializeDbConnectionSucceedsAsync()
    {
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        // Assert
        Assert.NotNull(db);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);
        var collections = db.GetCollectionsAsync();

        // Assert
        Assert.NotEmpty(collections.ToEnumerable());
        Assert.True(await collections.ContainsAsync(collection));
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanCheckIfCollectionExistsAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        string collection = "my_collection";
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);

        // Assert
        Assert.True(await db.DoesCollectionExistAsync("my_collection"));
        Assert.False(await db.DoesCollectionExistAsync("my_collection2"));
    }

    [Fact(Skip = SkipOrNot)]
    public async Task CreatingDuplicateCollectionDoesNothingAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);
        var collections = db.GetCollectionsAsync();
        await db.CreateCollectionAsync(collection);

        // Assert
        var collections2 = db.GetCollectionsAsync();
        Assert.Equal(await collections.CountAsync(), await collections.CountAsync());
    }

    [Fact(Skip = SkipOrNot)]
    public async Task CollectionsCanBeDeletedAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
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
        Assert.True(await collections2.CountAsync() == 0);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanInsertIntoNonExistentCollectionAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);

        // Arrange
        var key = await db.UpsertAsync("random collection", testRecord);
        var actual = await db.GetAsync("random collection", key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
        var actualDefault = await db.GetAsync(collection, key);
        var actualWithEmbedding = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actualDefault);
        Assert.NotNull(actualWithEmbedding);
        Assert.Empty(actualDefault.Embedding.Vector);
        Assert.NotEmpty(actualWithEmbedding.Embedding.Vector);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanUpsertAndRetrieveARecordWithNoTimestampAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
        var actual = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanUpsertAndRetrieveARecordWithTimestampAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
        var actual = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
        var actual = await db.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord2.Metadata.Id, actual.Key);
        Assert.NotEqual(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord2.Embedding.Vector, actual.Embedding.Vector);
        Assert.NotEqual(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord2.Metadata.Description, actual.Metadata.Description);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ExistingRecordCanBeRemovedAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
    }

    [Fact(Skip = SkipOrNot)]
    public async Task RemovingNonExistingRecordDoesNothingAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.CreateCollectionAsync(collection);
        await db.RemoveAsync(collection, "key");
        var actual = await db.GetAsync(collection, "key");

        // Assert
        Assert.Null(actual);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        string[] testCollections = { "random_collection1", "random_collection2", "random_collection3" };
        this._collectionNum += 3;
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

    [Fact(Skip = SkipOrNot)]
    public async Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
    }

    [Fact(Skip = SkipOrNot)]
    public async Task GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
        var topNResultDefault = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
        var topNResultWithEmbedding = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold, withEmbedding: true);

        // Assert
        Assert.NotNull(topNResultDefault);
        Assert.NotNull(topNResultWithEmbedding);
        Assert.Empty(topNResultDefault.Value.Item1.Embedding.Vector);
        Assert.NotEmpty(topNResultWithEmbedding.Value.Item1.Embedding.Vector);
    }

    [Fact(Skip = SkipOrNot)]
    public async Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
    }

    [Fact(Skip = SkipOrNot)]
    public async Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
        Assert.Equal(topN, topNKeys.Count());

        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanBatchUpsertRecordsAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanBatchGetRecordsAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
    }

    [Fact(Skip = SkipOrNot)]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
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
    }

    [Fact(Skip = SkipOrNot)]
    public async Task DeletingNonExistentCollectionDoesNothingAsync()
    {
        // Arrange
        using PostgresMemoryStore db = await this.CreateMemoryStoreAsync();
        string collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        await db.DeleteCollectionAsync(collection);
    }
}
