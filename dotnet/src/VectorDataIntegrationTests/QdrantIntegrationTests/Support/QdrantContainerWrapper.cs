// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using QdrantIntegrationTests.Support.TestContainer;

namespace QdrantIntegrationTests.Support;

public class QdrantContainerWrapper : IAsyncDisposable
{
    private static readonly QdrantContainer s_container = new QdrantBuilder().Build();
    private static QdrantClient? s_client;
    private static QdrantVectorStore? s_defaultVectorStore;

    private static readonly SemaphoreSlim s_lock = new(1, 1);
    private static int s_referenceCount;

    public QdrantClient Client => s_client ?? throw new InvalidOperationException("Not initialized");
    public QdrantVectorStore DefaultVectorStore => s_defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    private QdrantContainerWrapper()
    {
    }

    public static async Task<QdrantContainerWrapper> GetAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (s_referenceCount++ == 0)
            {
                await s_container.StartAsync();
                s_client = new QdrantClient(s_container.Hostname, s_container.GetMappedPublicPort(QdrantBuilder.QdrantGrpcPort));
                s_defaultVectorStore = new(s_client);
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
