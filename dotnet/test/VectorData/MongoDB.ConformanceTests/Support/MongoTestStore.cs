// Copyright (c) Microsoft. All rights reserved.

using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Configurations;
using DotNet.Testcontainers.Containers;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using MongoDB.Driver;
using Testcontainers.MongoDb;
using VectorData.ConformanceTests.Support;

namespace MongoDB.ConformanceTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class MongoTestStore : TestStore
{
    public static MongoTestStore Instance { get; } = new();

    private MongoDbContainer? _container;

    private MongoClient? _client;
    private IMongoDatabase? _database;

    public MongoClient Client => this._client ?? throw new InvalidOperationException("Not initialized");
    public IMongoDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public MongoVectorStore GetVectorStore(MongoVectorStoreOptions options)
        => new(this.Database, options);

    private MongoTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        var clientSettings = MongoTestEnvironment.IsConnectionInfoDefined
            ? MongoClientSettings.FromConnectionString(MongoTestEnvironment.ConnectionUrl)
            : await this.StartMongoDbContainerAsync();

        this._client = new MongoClient(clientSettings);
        this._database = this._client.GetDatabase("VectorSearchTests");
        this.DefaultVectorStore = new MongoVectorStore(this._database);
    }

    private async Task<MongoClientSettings> StartMongoDbContainerAsync()
    {
        this._container = new MongoDbBuilder()
            .WithImage("mongodb/mongodb-atlas-local:latest")
            .WithWaitStrategy(Wait.ForUnixContainer().AddCustomWaitStrategy(new WaitForVectorIndexService()))
            .Build();

        using CancellationTokenSource cts = new();
        cts.CancelAfter(TimeSpan.FromSeconds(60));
        await this._container.StartAsync(cts.Token);

        return new MongoClientSettings
        {
            Server = new MongoServerAddress(this._container.Hostname, this._container.GetMappedPublicPort(MongoDbBuilder.MongoDbPort)),
            DirectConnection = true,
            // ReadConcern = ReadConcern.Linearizable,
            // WriteConcern = WriteConcern.WMajority
        };
    }

    private static readonly string? s_baseObjectId = ObjectId.GenerateNewId().ToString().Substring(0, 14);

    public override TKey GenerateKey<TKey>(int value)
    {
        if (typeof(TKey) == typeof(ObjectId))
        {
            return (TKey)(object)ObjectId.Parse(s_baseObjectId + value.ToString("0000000000"));
        }

        return base.GenerateKey<TKey>(value);
    }

    protected override async Task StopAsync()
    {
        if (this._container != null)
        {
            await this._container.StopAsync();
            this._container = null;
        }
    }

    private sealed class WaitForVectorIndexService : IWaitUntil
    {
        public async Task<bool> UntilAsync(IContainer container)
        {
            var connectionString = $"mongodb://{container.Hostname}:{container.GetMappedPublicPort(27017).ToString()}?directConnection=true";
            using var client = new MongoClient(connectionString);
            var databaseName = Guid.NewGuid().ToString();
            var weGood = false;

            try
            {
                var database = client.GetDatabase(databaseName);
                var collectionName = Guid.NewGuid().ToString();
                await database.CreateCollectionAsync(collectionName);

                var model = new CreateSearchIndexModel(
                    Guid.NewGuid().ToString(),
                    SearchIndexType.VectorSearch,
                    BsonDocument.Parse(
                        """
                        {
                          "fields": [
                            {
                              "type": "vector",
                              "path": "Dummy",
                              "numDimensions": 8,
                              "similarity": "cosine"
                            }
                          ]
                        }
                        """));

                await database.GetCollection<BsonDocument>(collectionName).SearchIndexes.CreateOneAsync(model);
                weGood = true;
            }
            catch
            {
                // Intentionally ignored.
            }

            try
            {
                await client.DropDatabaseAsync(databaseName);
            }
            catch
            {
                // Intentionally ignored.
            }

            return weGood;
        }
    }
}
