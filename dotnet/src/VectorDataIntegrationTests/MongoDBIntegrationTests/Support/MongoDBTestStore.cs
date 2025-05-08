// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Driver;
using Testcontainers.MongoDb;
using VectorDataSpecificationTests.Support;

namespace MongoDBIntegrationTests.Support;

internal sealed class MongoDBTestStore : TestStore
{
    public static MongoDBTestStore Instance { get; } = new();

#pragma warning disable CA2213 // Disposable fields should be disposed
    private readonly MongoDbContainer _container = new MongoDbBuilder()
#pragma warning restore CA2213 // Disposable fields should be disposed
        .WithImage("mongodb/mongodb-atlas-local:7.0.6")
        .Build();

    public MongoClient? _client { get; private set; }
    public IMongoDatabase? _database { get; private set; }

    public MongoClient Client => this._client ?? throw new InvalidOperationException("Not initialized");
    public IMongoDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public MongoVectorStore GetVectorStore(MongoVectorStoreOptions options)
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
        this.DefaultVectorStore = new MongoVectorStore(this._database);
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
