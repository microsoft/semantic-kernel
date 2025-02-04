// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Driver;
using Testcontainers.MongoDb;

namespace MongoDBIntegrationTests.Support;

public class MongoDBContainerWrapper : IAsyncDisposable
{
    private static readonly MongoDbContainer s_container = new MongoDbBuilder()
        .WithImage("mongodb/mongodb-atlas-local:7.0.6")
        .Build();
    public static MongoClient? s_client { get; private set; }
    public static IMongoDatabase? s_database { get; private set; }
    private static MongoDBVectorStore? s_defaultVectorStore;

    private static readonly SemaphoreSlim s_lock = new(1, 1);
    private static int s_referenceCount;

    public MongoClient Client => s_client ?? throw new InvalidOperationException("Not initialized");
    public IMongoDatabase Databaes => s_database ?? throw new InvalidOperationException("Not initialized");
    public MongoDBVectorStore DefaultVectorStore => s_defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    private MongoDBContainerWrapper()
    {
    }

    public static async Task<MongoDBContainerWrapper> GetAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (s_referenceCount++ == 0)
            {
                await s_container.StartAsync();

                s_client = new MongoClient(new MongoClientSettings
                {
                    Server = new MongoServerAddress(s_container.Hostname, s_container.GetMappedPublicPort(MongoDbBuilder.MongoDbPort)),
                    DirectConnection = true,
                    // ReadConcern = ReadConcern.Linearizable,
                    // WriteConcern = WriteConcern.WMajority
                });
                s_database = s_client.GetDatabase("VectorSearchTests");
                s_defaultVectorStore = new(s_database);
            }
        }
        finally
        {
            s_lock.Release();
        }

        return new();
    }

    public async ValueTask DisposeAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (--s_referenceCount == 0)
            {
                await s_container.StopAsync();
            }
        }
        finally
        {
            s_lock.Release();
        }

        GC.SuppressFinalize(this);
    }
}
