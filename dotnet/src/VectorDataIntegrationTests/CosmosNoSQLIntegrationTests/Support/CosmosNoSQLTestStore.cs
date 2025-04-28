// Copyright (c) Microsoft. All rights reserved.

#if NET472
using System.Net.Http;
#endif
using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using VectorDataSpecificationTests.Support;

namespace CosmosNoSQLIntegrationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields (_connection) but is not disposable

internal sealed class CosmosNoSQLTestStore : TestStore
{
    public static CosmosNoSQLTestStore Instance { get; } = new();

    private CosmosClient? _client;
    private Database? _database;
    private AzureCosmosDBNoSQLVectorStore? _defaultVectorStore;

    public override string DefaultIndexKind => Microsoft.Extensions.VectorData.IndexKind.Flat;

    public CosmosClient Client
        => this._client ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public Database Database
        => this._database ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public override IVectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public AzureCosmosDBNoSQLVectorStore GetVectorStore(AzureCosmosDBNoSQLVectorStoreOptions options)
        => new(this.Database, options);

    private CosmosNoSQLTestStore()
    {
    }

#pragma warning disable CA5400 // HttpClient may be created without enabling CheckCertificateRevocationList
    protected override async Task StartAsync()
    {
        var connectionString = CosmosNoSQLTestEnvironment.ConnectionString;

        if (string.IsNullOrWhiteSpace(connectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the AzureCosmosDBNoSQL:ConnectionString environment variable");
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
        this._defaultVectorStore = new(this._database);
    }
#pragma warning restore CA5400
}
