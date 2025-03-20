// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using QdrantIntegrationTests.Support.TestContainer;
using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class QdrantTestStore : TestStore
{
    public static QdrantTestStore NamedVectorsInstance { get; } = new(hasNamedVectors: true);
    public static QdrantTestStore UnnamedVectorInstance { get; } = new(hasNamedVectors: false);

    private readonly QdrantContainer _container = new QdrantBuilder().Build();
    private readonly bool _hasNamedVectors;
    private QdrantClient? _client;
    private QdrantVectorStore? _defaultVectorStore;

    public QdrantClient Client => this._client ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public QdrantVectorStore GetVectorStore(QdrantVectorStoreOptions options)
        => new(this.Client, options);

    private QdrantTestStore(bool hasNamedVectors) => this._hasNamedVectors = hasNamedVectors;

    protected override async Task StartAsync()
    {
        await this._container.StartAsync();
        this._client = new QdrantClient(this._container.Hostname, this._container.GetMappedPublicPort(QdrantBuilder.QdrantGrpcPort));
        this._defaultVectorStore = new(this._client, new() { HasNamedVectors = this._hasNamedVectors });
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
