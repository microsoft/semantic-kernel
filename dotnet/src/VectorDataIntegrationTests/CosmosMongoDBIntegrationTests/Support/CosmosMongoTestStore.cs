﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosMongoDB;
using MongoDB.Driver;
using VectorDataSpecificationTests.Support;

namespace CosmosMongoDBIntegrationTests.Support;

public sealed class CosmosMongoTestStore : TestStore
{
    public static CosmosMongoTestStore Instance { get; } = new();

    private MongoClient? _client;
    private IMongoDatabase? _database;
    private CosmosMongoVectorStore? _defaultVectorStore;

    public MongoClient Client => this._client ?? throw new InvalidOperationException("Not initialized");
    public IMongoDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public override VectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public override string DefaultIndexKind => Microsoft.Extensions.VectorData.IndexKind.IvfFlat;

    public override string DefaultDistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    public CosmosMongoVectorStore GetVectorStore(CosmosMongoVectorStoreOptions options)
        => new(this.Database, options);

    private CosmosMongoTestStore()
    {
    }

    protected override Task StartAsync()
    {
        if (string.IsNullOrWhiteSpace(CosmosMongoTestEnvironment.ConnectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the CosmosMongo:ConnectionString environment variable");
        }

        this._client = new MongoClient(CosmosMongoTestEnvironment.ConnectionString);
        this._database = this._client.GetDatabase("VectorSearchTests");
        this._defaultVectorStore = new(this._database);

        return Task.CompletedTask;
    }
}
