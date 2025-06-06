// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Driver;
using Testcontainers.MongoDb;
using VectorData.ConformanceTests.Support;

namespace MongoDB.ConformanceTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class MongoTestStore : TestStore
{
    public static MongoTestStore Instance { get; } = new();

    private readonly MongoDbContainer _container = new MongoDbBuilder()
        .WithImage("mongodb/mongodb-atlas-local:7.0.6")
        .Build();

    public MongoClient? _client { get; private set; }
    public IMongoDatabase? _database { get; private set; }

    public MongoClient Client => this._client ?? throw new InvalidOperationException("Not initialized");
    public IMongoDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public MongoVectorStore GetVectorStore(MongoVectorStoreOptions options)
        => new(this.Database, options);

    private MongoTestStore()
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
