// Copyright (c) Microsoft. All rights reserved.

#if NET472
using System.Net.Http;
#endif
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support.TestContainer;

namespace WeaviateIntegrationTests.Support;

public sealed class WeaviateTestStore : TestStore
{
    public static WeaviateTestStore Instance { get; } = new();

    private readonly WeaviateContainer _container = new WeaviateBuilder().Build();
    public HttpClient? _httpClient { get; private set; }
    private WeaviateVectorStore? _defaultVectorStore;

    public HttpClient Client => this._httpClient ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public WeaviateVectorStore GetVectorStore(WeaviateVectorStoreOptions options)
        => new(this.Client, options);

    private WeaviateTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        await this._container.StartAsync();
        this._httpClient = new HttpClient { BaseAddress = new Uri($"http://localhost:{this._container.GetMappedPublicPort(WeaviateBuilder.WeaviateHttpPort)}/v1/") };
        this._defaultVectorStore = new(this._httpClient);
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
