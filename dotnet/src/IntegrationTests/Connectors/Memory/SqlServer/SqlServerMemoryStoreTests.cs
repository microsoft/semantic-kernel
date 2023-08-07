// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.SqlServer;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.SqlServer;

/// <summary>
/// Integration tests of <see cref="SqlServerMemoryStore"/>.
/// </summary>
public class SqlServerMemoryStoreTests : IAsyncLifetime
{
    // If null, all tests will be enabled
    private const string? SkipReason = "Requires SqlServer server up and running";

    public async Task InitializeAsync()
    {
        // Load configuration
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SqlServerMemoryStoreTests>()
            .Build();

        var connectionString = configuration["SqlServer:ConnectionString"];

        if (string.IsNullOrWhiteSpace(connectionString))
        {
            throw new ArgumentNullException("SqlServer memory connection string is not configured");
        }

        this._connectionString = connectionString;

        this._dataSource = new SqlServerClient(connectionString, "dbo");

        await this._dataSource.CreateTables(CancellationToken.None).ConfigureAwait(false);
    }

    [Fact(Skip = SkipReason)]
    public void InitializeDbConnectionSucceeds()
    {
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        // Assert
        Assert.NotNull(memoryStore);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        string collection = "test_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var collections = memoryStore.GetCollectionsAsync();

        // Assert
        Assert.NotEmpty(collections.ToEnumerable());
        Assert.True(await collections.ContainsAsync(collection));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCheckIfCollectionExistsAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        string collection = "my_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);

        // Assert
        Assert.True(await memoryStore.DoesCollectionExistAsync("my_collection"));
        Assert.False(await memoryStore.DoesCollectionExistAsync("my_collection2"));
    }

    [Fact(Skip = SkipReason)]
    public async Task CollectionsCanBeDeletedAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        string collection = "test_collection";
        await memoryStore.CreateCollectionAsync(collection);
        Assert.True(await memoryStore.DoesCollectionExistAsync(collection));

        // Act
        await memoryStore.DeleteCollectionAsync(collection);

        // Assert
        Assert.False(await memoryStore.DoesCollectionExistAsync(collection));
    }

    [Fact(Skip = SkipReason)]
    public async Task GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);
        string collection = "test_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var key = await memoryStore.UpsertAsync(collection, testRecord);
        var actualDefault = await memoryStore.GetAsync(collection, key);
        var actualWithEmbedding = await memoryStore.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actualDefault);
        Assert.NotNull(actualWithEmbedding);
        Assert.Empty(actualDefault.Embedding.Vector);
        Assert.NotEmpty(actualWithEmbedding.Embedding.Vector);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveARecordWithNoTimestampAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);
        string collection = "test_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var key = await memoryStore.UpsertAsync(collection, testRecord);
        var actual = await memoryStore.GetAsync(collection, key, true);

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

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveARecordWithTimestampAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: DateTimeOffset.FromUnixTimeMilliseconds(DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()));
        string collection = "test_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var key = await memoryStore.UpsertAsync(collection, testRecord);
        var actual = await memoryStore.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
        Assert.Equal(testRecord.Timestamp, actual.Timestamp);
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
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
        string collection = "test_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var key = await memoryStore.UpsertAsync(collection, testRecord);
        var key2 = await memoryStore.UpsertAsync(collection, testRecord2);
        var actual = await memoryStore.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord2.Metadata.Id, actual.Key);
        Assert.NotEqual(testRecord.Embedding.Vector, actual.Embedding.Vector);
        Assert.Equal(testRecord2.Embedding.Vector, actual.Embedding.Vector);
        Assert.NotEqual(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord2.Metadata.Description, actual.Metadata.Description);
    }

    [Fact(Skip = SkipReason)]
    public async Task ExistingRecordCanBeRemovedAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        string collection = "test_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var key = await memoryStore.UpsertAsync(collection, testRecord);
        var upsertedRecord = await memoryStore.GetAsync(collection, key);
        await memoryStore.RemoveAsync(collection, key);
        var actual = await memoryStore.GetAsync(collection, key);

        // Assert
        Assert.NotNull(upsertedRecord);
        Assert.Null(actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task RemovingNonExistingRecordDoesNothingAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        string collection = "test_collection";

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        await memoryStore.RemoveAsync(collection, "key");
        var actual = await memoryStore.GetAsync(collection, "key");

        // Assert
        Assert.Null(actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        string[] testCollections = { "random_collection1", "random_collection2", "random_collection3" };
        await memoryStore.CreateCollectionAsync(testCollections[0]);
        await memoryStore.CreateCollectionAsync(testCollections[1]);
        await memoryStore.CreateCollectionAsync(testCollections[2]);

        // Act
        var collections = await memoryStore.GetCollectionsAsync().ToListAsync();

        // Assert
        foreach (var collection in testCollections)
        {
            Assert.True(await memoryStore.DoesCollectionExistAsync(collection));
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

    [Fact(Skip = SkipReason)]
    public async Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection";
        await memoryStore.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        // Act
        double threshold = -1;
        var topNResults = memoryStore.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        for (int j = 0; j < topN - 1; j++)
        {
            int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
            Assert.True(compare >= 0);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        string collection = "test_collection";
        await memoryStore.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        // Act
        double threshold = 0.75;
        var topNResultDefault = await memoryStore.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
        var topNResultWithEmbedding = await memoryStore.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold, withEmbedding: true);

        // Assert
        Assert.NotNull(topNResultDefault);
        Assert.NotNull(topNResultWithEmbedding);
        Assert.Empty(topNResultDefault.Value.Item1.Embedding.Vector);
        Assert.NotEmpty(topNResultWithEmbedding.Value.Item1.Embedding.Vector);
    }

    [Fact(Skip = SkipReason)]
    public async Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        string collection = "test_collection";
        await memoryStore.CreateCollectionAsync(collection);
        int i = 0;
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        i++;
        testRecord = MemoryRecord.LocalRecord(
            id: "test" + i,
            text: "text" + i,
            description: "description" + i,
            embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
        _ = await memoryStore.UpsertAsync(collection, testRecord);

        // Act
        double threshold = 0.75;
        var topNResult = await memoryStore.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);

        // Assert
        Assert.NotNull(topNResult);
        Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
        Assert.True(topNResult.Value.Item2 >= threshold);
    }

    [Fact(Skip = SkipReason)]
    public async Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
        int topN = 4;
        string collection = "test_collection";
        await memoryStore.CreateCollectionAsync(collection);

        for (int i = 0; i < 10; i++)
        {
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await memoryStore.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResults = memoryStore.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();
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

    [Fact(Skip = SkipReason)]
    public async Task ItCanBatchUpsertRecordsAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        int numRecords = 10;
        string collection = "test_collection";
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var keys = memoryStore.UpsertBatchAsync(collection, records);
        var resultRecords = memoryStore.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.Equal(numRecords, keys.ToEnumerable().Count());
        Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanBatchGetRecordsAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        int numRecords = 10;
        string collection = "test_collection";
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        var keys = memoryStore.UpsertBatchAsync(collection, records);

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var results = memoryStore.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.NotNull(results);
        Assert.Equal(numRecords, results.ToEnumerable().Count());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        int numRecords = 10;
        string collection = "test_collection";
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        await memoryStore.CreateCollectionAsync(collection);

        List<string> keys = new();

        // Act
        await foreach (var key in memoryStore.UpsertBatchAsync(collection, records))
        {
            keys.Add(key);
        }

        await memoryStore.RemoveBatchAsync(collection, keys);

        // Assert
        await foreach (var result in memoryStore.GetBatchAsync(collection, keys))
        {
            Assert.Null(result);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task DeletingNonExistentCollectionDoesNothingAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        string collection = "test_collection";

        // Act
        await memoryStore.DeleteCollectionAsync(collection);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanBatchGetRecordsAndSkipIfKeysDoNotExistAsync()
    {
        // Arrange
        SqlServerMemoryStore memoryStore = this.CreateMemoryStore();
        int numRecords = 10;
        string collection = "test_collection";
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

        // Act
        await memoryStore.CreateCollectionAsync(collection);
        var keys = await memoryStore.UpsertBatchAsync(collection, records).ToListAsync();
        keys.Insert(0, "not-exist-key-0");
        keys.Insert(5, "not-exist-key-5");
        keys.Add("not-exist-key-n");
        var resultRecords = memoryStore.GetBatchAsync(collection, keys);

        // Assert
        Assert.NotNull(keys);
        Assert.Equal(numRecords, keys.Count - 3);
        Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
    }

    #region private ================================================================================

    private string _connectionString = null!;
    private SqlServerClient _dataSource = null!;

    private SqlServerMemoryStore CreateMemoryStore()
    {
        return new SqlServerMemoryStore(this._dataSource);
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

    public async Task DisposeAsync()
    {
        await foreach (var item in this._dataSource.GetCollectionsAsync(CancellationToken.None).ConfigureAwait(false))
        {
            await this._dataSource.DeleteCollectionAsync(item, CancellationToken.None).ConfigureAwait(false);
        }
    }

    #endregion
}
