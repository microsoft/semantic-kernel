// Copyright (c) Microsoft. All rights reserved.

#if NET472
using System.Net.Http;
#endif
using Microsoft.SemanticKernel.Connectors.Weaviate;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support.TestContainer;

namespace Weaviate.ConformanceTests.Support;

#pragma warning restore CA2213 // Disposable fields should be disposed

public sealed class WeaviateTestStore : TestStore
{
    public static WeaviateTestStore NamedVectorsInstance { get; } = new(hasNamedVectors: true);
    public static WeaviateTestStore UnnamedVectorInstance { get; } = new(hasNamedVectors: false);

    public override string DefaultDistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    private readonly WeaviateContainer _container = new WeaviateBuilder().Build();
    private readonly bool _hasNamedVectors;
    public HttpClient? _httpClient { get; private set; }

    public HttpClient Client => this._httpClient ?? throw new InvalidOperationException("Not initialized");

    public WeaviateVectorStore GetVectorStore(WeaviateVectorStoreOptions options)
        => new(this.Client, options);

    private WeaviateTestStore(bool hasNamedVectors) => this._hasNamedVectors = hasNamedVectors;

    protected override async Task StartAsync()
    {
        await this._container.StartAsync();
        this._httpClient = new HttpClient { BaseAddress = new Uri($"http://localhost:{this._container.GetMappedPublicPort(WeaviateBuilder.WeaviateHttpPort)}/v1/") };
        this.DefaultVectorStore = new WeaviateVectorStore(this._httpClient, new() { HasNamedVectors = this._hasNamedVectors });
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
