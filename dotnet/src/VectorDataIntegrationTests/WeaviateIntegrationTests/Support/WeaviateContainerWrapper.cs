// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Weaviate;
using WeaviateIntegrationTests.Support.TestContainer;

namespace WeaviateIntegrationTests.Support;

public class WeaviateContainerWrapper : IAsyncDisposable
{
    private static readonly WeaviateContainer s_container = new WeaviateBuilder().Build();
    public static HttpClient? s_httpClient { get; private set; }
    private static WeaviateVectorStore? s_defaultVectorStore;

    private static readonly SemaphoreSlim s_lock = new(1, 1);
    private static int s_referenceCount;

    public HttpClient Client => s_httpClient ?? throw new InvalidOperationException("Not initialized");
    public WeaviateVectorStore DefaultVectorStore => s_defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    private WeaviateContainerWrapper()
    {
    }

    public static async Task<WeaviateContainerWrapper> GetAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (s_referenceCount++ == 0)
            {
                await s_container.StartAsync();
                s_httpClient = new HttpClient { BaseAddress = new Uri($"http://localhost:{s_container.GetMappedPublicPort(WeaviateBuilder.WeaviateHttpPort)}/v1/") };
                s_defaultVectorStore = new(s_httpClient);
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
