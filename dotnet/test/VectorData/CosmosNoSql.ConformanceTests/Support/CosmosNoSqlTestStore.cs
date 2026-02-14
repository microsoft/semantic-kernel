// Copyright (c) Microsoft. All rights reserved.

#if NET472
using System.Net.Http;
#endif
// using System.Globalization;
using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using VectorData.ConformanceTests.Support;

namespace CosmosNoSql.ConformanceTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields (_connection) but is not disposable
#pragma warning disable CA2000 // Dispose objects before losing scope

internal sealed class CosmosNoSqlTestStore : TestStore
{
    public static CosmosNoSqlTestStore Instance { get; } = new();

    private CosmosClient? _client;
    private Database? _database;

    public override string DefaultIndexKind => Microsoft.Extensions.VectorData.IndexKind.Flat;

    public CosmosClient Client
        => this._client ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public Database Database
        => this._database ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public CosmosNoSqlVectorStore GetVectorStore(CosmosNoSqlVectorStoreOptions options)
        => new(this.Database, options);

    private CosmosNoSqlTestStore()
    {
    }

    public override VectorStoreCollection<TKey, TRecord> CreateCollection<TKey, TRecord>(
        string name,
        VectorStoreCollectionDefinition definition)
    {
        // Cosmos NoSQL requires specifying a partition key for container creation.
        // For the tests, use the key property as the partition key.
        var keyPropertyName = definition.Properties.OfType<VectorStoreKeyProperty>().FirstOrDefault()?.Name
            ?? throw new InvalidOperationException("Definition must have a key property");

        var options = new CosmosNoSqlCollectionOptions
        {
            Definition = definition,
            PartitionKeyPropertyNames = [keyPropertyName],
            EmbeddingGenerator = definition.EmbeddingGenerator
        };

        // Also, in Cosmos NoSQL there's a discrepancy between:
        // 1. The key property in the model and on the record type (representing the Cosmos document ID - string or Guid)
        // 2. The TKey generic type variable on the collection (must be CosmosNoSqlKey, wrapping both the document ID and the partition key)
        // To bridge this gap in the tests, if the test expects a simpler key type (string, Guid), we wrap it in an adapter that translates between the two.
        var collection = new CosmosNoSqlCollection<CosmosNoSqlKey, TRecord>(this.Database, name, options);

        return typeof(TKey) switch
        {
            var t when t == typeof(CosmosNoSqlKey)
                => (VectorStoreCollection<TKey, TRecord>)(object)collection,

            var t when t == typeof(string)
                => (VectorStoreCollection<TKey, TRecord>)(object)new CosmosNoSqlCollectionAdapter<string, TRecord>(collection),
            var t when t == typeof(Guid)
                => (VectorStoreCollection<TKey, TRecord>)(object)new CosmosNoSqlCollectionAdapter<Guid, TRecord>(collection),

            _ => throw new InvalidOperationException(
                $"Cosmos NoSQL tests must use string, Guid or CosmosNoSqlKey as the key type. Got: {typeof(TKey).Name}")
        };
    }

    public override VectorStoreCollection<object, Dictionary<string, object?>> CreateDynamicCollection(
        string name,
        VectorStoreCollectionDefinition definition)
    {
        // See notes in CreateCollection above.
        var keyPropertyName = definition.Properties.OfType<VectorStoreKeyProperty>().FirstOrDefault()?.Name
            ?? throw new InvalidOperationException("Definition must have a key property");

        return new CosmosNoSqlDynamicCollectionAdapter(
            new CosmosNoSqlDynamicCollection(
                this.Database,
                name,
                new CosmosNoSqlCollectionOptions
                {
                    Definition = definition,
                    PartitionKeyPropertyNames = [keyPropertyName]
                }));
    }

#pragma warning disable CA5400 // HttpClient may be created without enabling CheckCertificateRevocationList
    protected override async Task StartAsync()
    {
        var connectionString = CosmosNoSqlTestEnvironment.ConnectionString;

        if (string.IsNullOrWhiteSpace(connectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the CosmosNoSql:ConnectionString environment variable");
        }

        var options = new CosmosClientOptions
        {
            UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default,
            ConnectionMode = ConnectionMode.Gateway,
            HttpClientFactory = () => new HttpClient(new HttpClientHandler { ServerCertificateCustomValidationCallback = HttpClientHandler.DangerousAcceptAnyServerCertificateValidator })
        };

        this._client = new CosmosClient(connectionString, options);
        this._database = this._client.GetDatabase("VectorDataIntegrationTests");
        await this._client.CreateDatabaseIfNotExistsAsync("VectorDataIntegrationTests");
        this.DefaultVectorStore = new CosmosNoSqlVectorStore(this._database);
    }
#pragma warning restore CA5400

    protected override Task StopAsync()
    {
        this._client?.Dispose();
        return base.StopAsync();
    }
}
