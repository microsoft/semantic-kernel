// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Driver;
using Testcontainers.MongoDb;
using VectorDataSpecificationTests.Support;

namespace MongoDBIntegrationTests.Support;

internal sealed class MongoDBTestStore : TestStore
{
    public static MongoDBTestStore Instance { get; } = new();

    private readonly MongoDbContainer _container = new MongoDbBuilder()
        .WithImage("mongodb/mongodb-atlas-local:7.0.6")
        .Build();

    public MongoClient? _client { get; private set; }
    public IMongoDatabase? _database { get; private set; }
    private MongoDBVectorStore? _defaultVectorStore;

    public MongoClient Client => this._client ?? throw new InvalidOperationException("Not initialized");
    public IMongoDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public MongoDBVectorStore GetVectorStore(MongoDBVectorStoreOptions options)
        => new(this.Database, options);

    private MongoDBTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        using CancellationTokenSource cts = new();
        cts.CancelAfter(TimeSpan.FromSeconds(60));
        await this._container.StartAsync(cts.Token);

        this._client = new MongoClient(new MongoClientSettings
        {
            Server = new MongoServerAddress(this._container.Hostname, this._container.GetMappedPublicPort(MongoDbBuilder.MongoDbPort)),
            DirectConnection = true,
            // ReadConcern = ReadConcern.Linearizable,
            // WriteConcern = WriteConcern.WMajority
        });
        this._database = this._client.GetDatabase("VectorSearchTests");
        this._defaultVectorStore = new(this._database);
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
