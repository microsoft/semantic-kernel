// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.SqlServer;

/// <summary>
/// Unit tests for <see cref="SqlServerMemoryStore"/> class.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class SqlServerMemoryStoreTests : IAsyncLifetime
{
    private const string? SkipReason = "Configure SQL Server or Azure SQL connection string and then set this to 'null'.";
    //private const string? SkipReason = null;
    private const string SchemaName = "sk_it";
    private const string DefaultCollectionName = "test";
    private const int TestEmbeddingDimensionsCount = 5;

    private string _connectionString = null!;

    private SqlServerMemoryStore Store { get; set; } = null!;

    public async Task InitializeAsync()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SqlServerMemoryStore>()
            .Build();

        this._connectionString = configuration["SqlServer:ConnectionString"]
            ?? throw new ArgumentException("SqlServer memory connection string is not configured.");

        await this.CleanupDatabaseAsync();
        await this.InitializeDatabaseAsync();

        this.Store = new SqlServerMemoryStore(this._connectionString, SchemaName, TestEmbeddingDimensionsCount);
    }

    public async Task DisposeAsync()
    {
        await this.CleanupDatabaseAsync();
    }

    [Fact(Skip = SkipReason)]
    public async Task CreateCollectionAsync()
    {
        Assert.False(await this.Store.DoesCollectionExistAsync(DefaultCollectionName));

        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        Assert.True(await this.Store.DoesCollectionExistAsync(DefaultCollectionName));
    }

    [Fact(Skip = SkipReason)]
    public async Task DropCollectionAsync()
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.Store.DeleteCollectionAsync(DefaultCollectionName);
        Assert.False(await this.Store.DoesCollectionExistAsync(DefaultCollectionName));
    }

    [Fact(Skip = SkipReason)]
    public async Task GetCollectionsAsync()
    {
        await this.Store.CreateCollectionAsync("collection1");
        await this.Store.CreateCollectionAsync("collection2");

        var collections = await this.Store.GetCollectionsAsync().ToArrayAsync();
        Assert.Contains("collection1", collections);
        Assert.Contains("collection2", collections);
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertAsync()
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);

        var id = await this.Store.UpsertAsync(DefaultCollectionName, new MemoryRecord(
            new MemoryRecordMetadata(
                isReference: true,
                id: "Some id",
                description: "Some description",
                text: "Some text",
                externalSourceName: "Some external resource name",
                additionalMetadata: "Some additional metadata"),
            new[] { 10f, 11f, 12f, 13f, 14f },
            key: "Some key",
            timestamp: new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero)));

        Assert.Equal("Some id", id);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.InsertSampleDataAsync();

        var record = await this.Store.GetAsync(DefaultCollectionName, "Some id", withEmbedding: withEmbeddings);
        Assert.NotNull(record);

        Assert.True(record.Metadata.IsReference);
        Assert.Equal("Some id", record.Metadata.Id);
        Assert.Equal("Some description", record.Metadata.Description);
        Assert.Equal("Some text", record.Metadata.Text);
        Assert.Equal("Some external resource name", record.Metadata.ExternalSourceName);
        Assert.Equal("Some additional metadata", record.Metadata.AdditionalMetadata);
        Assert.Equal(new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero), record.Timestamp);

        Assert.Equal(
            withEmbeddings ? [10f, 11f, 12f, 13f, 14f] : [],
            record.Embedding.ToArray());
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertBatchAsync()
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        var ids = await this.InsertSampleDataAsync();

        Assert.Collection(ids,
            id => Assert.Equal("Some id", id),
            id => Assert.Equal("Some other id", id));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetBatchAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.InsertSampleDataAsync();

        var records = this.Store.GetBatchAsync(DefaultCollectionName, ["Some id", "Some other id"], withEmbeddings: withEmbeddings).ToEnumerable().ToList();

        Assert.Collection(records.OrderBy(r => r.Metadata.Id),
            r =>
            {
                Assert.True(r.Metadata.IsReference);
                Assert.Equal("Some id", r.Metadata.Id);
                Assert.Equal("Some description", r.Metadata.Description);
                Assert.Equal("Some text", r.Metadata.Text);
                Assert.Equal("Some external resource name", r.Metadata.ExternalSourceName);
                Assert.Equal("Some additional metadata", r.Metadata.AdditionalMetadata);
                Assert.Equal(new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero), r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [10f, 11f, 12f, 13f, 14f] : [],
                    r.Embedding.ToArray());
            },
            r =>
            {
                Assert.False(r.Metadata.IsReference);
                Assert.Equal("Some other id", r.Metadata.Id);
                Assert.Empty(r.Metadata.Description);
                Assert.Empty(r.Metadata.Text);
                Assert.Empty(r.Metadata.ExternalSourceName);
                Assert.Empty(r.Metadata.AdditionalMetadata);
                Assert.Null(r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [20f, 21f, 22f, 23f, 24f] : [],
                    r.Embedding.ToArray());
            });
    }

    [Fact(Skip = SkipReason)]
    public async Task RemoveAsync()
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.InsertSampleDataAsync();

        Assert.NotNull(await this.Store.GetAsync(DefaultCollectionName, "Some id"));
        await this.Store.RemoveAsync(DefaultCollectionName, "Some id");
        Assert.Null(await this.Store.GetAsync(DefaultCollectionName, "Some id"));
    }

    [Fact(Skip = SkipReason)]
    public async Task RemoveBatchAsync()
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.InsertSampleDataAsync();

        Assert.NotNull(await this.Store.GetAsync(DefaultCollectionName, "Some id"));
        Assert.NotNull(await this.Store.GetAsync(DefaultCollectionName, "Some other id"));
        await this.Store.RemoveBatchAsync(DefaultCollectionName, ["Some id", "Some other id"]);
        Assert.Null(await this.Store.GetAsync(DefaultCollectionName, "Some id"));
        Assert.Null(await this.Store.GetAsync(DefaultCollectionName, "Some other id"));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetNearestMatchesAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.InsertSampleDataAsync();

        (MemoryRecord Record, double SimilarityScore)[] results =
            await this.Store.GetNearestMatchesAsync(DefaultCollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2, withEmbeddings: withEmbeddings).ToArrayAsync();

        Assert.All(results, t => Assert.True(t.SimilarityScore > 0));

        Assert.Collection(results.Select(r => r.Record),
            r =>
            {
                Assert.True(r.Metadata.IsReference);
                Assert.Equal("Some id", r.Metadata.Id);
                Assert.Equal("Some description", r.Metadata.Description);
                Assert.Equal("Some text", r.Metadata.Text);
                Assert.Equal("Some external resource name", r.Metadata.ExternalSourceName);
                Assert.Equal("Some additional metadata", r.Metadata.AdditionalMetadata);
                Assert.Equal(new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero), r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [10f, 11f, 12f, 13f, 14f] : [],
                    r.Embedding.ToArray());
            },
            r =>
            {
                Assert.False(r.Metadata.IsReference);
                Assert.Equal("Some other id", r.Metadata.Id);
                Assert.Empty(r.Metadata.Description);
                Assert.Empty(r.Metadata.Text);
                Assert.Empty(r.Metadata.ExternalSourceName);
                Assert.Empty(r.Metadata.AdditionalMetadata);
                Assert.Null(r.Timestamp);

                Assert.Equal(
                    withEmbeddings ? [20f, 21f, 22f, 23f, 24f] : [],
                    r.Embedding.ToArray());
            });
    }

    [Fact(Skip = SkipReason)]
    public async Task GetNearestMatchesWithMinRelevanceScoreAsync()
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.InsertSampleDataAsync();

        (MemoryRecord Record, double SimilarityScore)[] results =
            await this.Store.GetNearestMatchesAsync(DefaultCollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2).ToArrayAsync();

        var firstId = results[0].Record.Metadata.Id;
        var firstSimilarityScore = results[0].SimilarityScore;

        results = await this.Store.GetNearestMatchesAsync(DefaultCollectionName, new[] { 5f, 6f, 7f, 8f, 9f }, limit: 2, minRelevanceScore: firstSimilarityScore + 0.0001).ToArrayAsync();

        Assert.DoesNotContain(firstId, results.Select(r => r.Record.Metadata.Id));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetNearestMatchAsync(bool withEmbeddings)
    {
        await this.Store.CreateCollectionAsync(DefaultCollectionName);
        await this.InsertSampleDataAsync();

        (MemoryRecord Record, double SimilarityScore)? result =
            await this.Store.GetNearestMatchAsync(DefaultCollectionName, new[] { 20f, 21f, 22f, 23f, 24f }, withEmbedding: withEmbeddings);

        Assert.NotNull(result);
        Assert.True(result.Value.SimilarityScore > 0);
        MemoryRecord record = result.Value.Record;

        Assert.Equal("Some other id", record.Metadata.Id);
        Assert.Equal(
            withEmbeddings ? [20f, 21f, 22f, 23f, 24f] : [],
            record.Embedding.ToArray());
    }

    private async Task<List<string>> InsertSampleDataAsync()
    {
        var ids = this.Store.UpsertBatchAsync(DefaultCollectionName,
        [
            new MemoryRecord(
                new MemoryRecordMetadata(
                    isReference: true,
                    id: "Some id",
                    description: "Some description",
                    text: "Some text",
                    externalSourceName: "Some external resource name",
                    additionalMetadata: "Some additional metadata"),
                new[] { 10f, 11f, 12f, 13f, 14f },
                key: "Some key",
                timestamp: new DateTimeOffset(2023, 1, 1, 12, 0, 0, TimeSpan.Zero)),
            new MemoryRecord(
                new MemoryRecordMetadata(
                    isReference: false,
                    id: "Some other id",
                    description: "",
                    text: "",
                    externalSourceName: "",
                    additionalMetadata: ""),
                new[] { 20f, 21f, 22f, 23f, 24f },
                key: null,
                timestamp: null),
        ]);

        var idList = new List<string>();
        await foreach (var id in ids)
        {
            idList.Add(id);
        }
        return idList;
    }

    private async Task InitializeDatabaseAsync()
    {
#if NET // IAsyncDisposable is not present in Full Framework
        await using var connection = new SqlConnection(this._connectionString);
        await using var cmd = connection.CreateCommand();
#else
        using var connection = new SqlConnection(this._connectionString);
        using var cmd = connection.CreateCommand();
#endif

        await connection.OpenAsync();
        cmd.CommandText = $"CREATE SCHEMA {SchemaName}";
        await cmd.ExecuteNonQueryAsync();
    }

    private async Task CleanupDatabaseAsync()
    {
#if NET
        await using var connection = new SqlConnection(this._connectionString);
        await using var cmd = connection.CreateCommand();
#else
        using var connection = new SqlConnection(this._connectionString);
        using var cmd = connection.CreateCommand();
#endif
        await connection.OpenAsync();
        cmd.CommandText = $"""
            DECLARE tables_cursor CURSOR FOR
            SELECT table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
                AND table_schema = '{SchemaName}'
            ;

            DECLARE @table_name sysname;
            OPEN tables_cursor;
            FETCH NEXT FROM tables_cursor INTO @table_name;
            WHILE @@FETCH_STATUS = 0
            BEGIN
                EXEC ('DROP TABLE {SchemaName}.' + @table_name);
                FETCH NEXT FROM tables_cursor INTO @table_name;
            END;
            CLOSE tables_cursor;

            DEALLOCATE tables_cursor;

            DROP SCHEMA IF EXISTS {SchemaName};
            """;
        await cmd.ExecuteNonQueryAsync();
    }
}
