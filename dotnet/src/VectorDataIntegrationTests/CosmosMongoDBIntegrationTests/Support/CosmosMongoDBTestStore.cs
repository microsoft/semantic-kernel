// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using MongoDB.Driver;
using VectorDataSpecificationTests.Support;

namespace CosmosMongoDBIntegrationTests.Support;

public sealed class CosmosMongoDBTestStore : TestStore
{
    public static CosmosMongoDBTestStore Instance { get; } = new();

    private MongoClient? _client;
    private IMongoDatabase? _database;
    private AzureCosmosDBMongoDBVectorStore? _defaultVectorStore;

    public MongoClient Client => this._client ?? throw new InvalidOperationException("Not initialized");
    public IMongoDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public override string DefaultIndexKind => Microsoft.Extensions.VectorData.IndexKind.IvfFlat;

    public override string DefaultDistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    public AzureCosmosDBMongoDBVectorStore GetVectorStore(AzureCosmosDBMongoDBVectorStoreOptions options)
        => new(this.Database, options);

    private CosmosMongoDBTestStore()
    {
    }

    protected override Task StartAsync()
    {
        if (string.IsNullOrWhiteSpace(CosmosMongoDBTestEnvironment.ConnectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the AzureCosmosDBMongoDB:ConnectionString environment variable");
        }

        this._client = new MongoClient(CosmosMongoDBTestEnvironment.ConnectionString);
        this._database = this._client.GetDatabase("VectorSearchTests");
        this._defaultVectorStore = new(this._database);

        return Task.CompletedTask;
    }
}
