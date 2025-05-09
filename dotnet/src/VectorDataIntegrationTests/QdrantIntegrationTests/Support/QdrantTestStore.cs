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

    // Qdrant doesn't support the default Flat index kind
    public override string DefaultIndexKind => IndexKind.Hnsw;

#pragma warning disable CA2213 // Disposable fields should be disposed
    private readonly QdrantContainer _container = new QdrantBuilder().Build();
#pragma warning restore CA2213 // Disposable fields should be disposed
    private readonly bool _hasNamedVectors;
    private QdrantClient? _client;

    public QdrantClient Client => this._client ?? throw new InvalidOperationException("Not initialized");

    protected override void Dispose(bool disposing)
    {
        this._client?.Dispose();
        base.Dispose(disposing);
    }

    public QdrantVectorStore GetVectorStore(QdrantVectorStoreOptions options)
        => new(this.Client, new()
        {
            OwnsClient = false, // The client is shared, it's not owned by the vector store.
            HasNamedVectors = options.HasNamedVectors,
            EmbeddingGenerator = options.EmbeddingGenerator
        });

    private QdrantTestStore(bool hasNamedVectors) => this._hasNamedVectors = hasNamedVectors;

    /// <summary>
    /// Qdrant normalizes vectors on upsert, so we cannot compare
    /// what we upserted and what we retrieve, we can only check
    /// that a vector was returned.
    /// https://github.com/qdrant/qdrant-client/discussions/727
    /// </summary>
    public override bool VectorsComparable => false;

    protected override async Task StartAsync()
    {
        await this._container.StartAsync();
        this._client = new QdrantClient(this._container.Hostname, this._container.GetMappedPublicPort(QdrantBuilder.QdrantGrpcPort));
        // The client is shared, it's not owned by the vector store.
        this.DefaultVectorStore = new QdrantVectorStore(this._client, new() { HasNamedVectors = this._hasNamedVectors, OwnsClient = false });
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
