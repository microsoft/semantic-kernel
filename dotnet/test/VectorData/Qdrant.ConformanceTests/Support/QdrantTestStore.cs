// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using Testcontainers.Qdrant;
using VectorData.ConformanceTests.Support;

namespace Qdrant.ConformanceTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class QdrantTestStore : TestStore
{
    public static QdrantTestStore NamedVectorsInstance { get; } = new(hasNamedVectors: true);
    public static QdrantTestStore UnnamedVectorInstance { get; } = new(hasNamedVectors: false);

    // Qdrant doesn't support the default Flat index kind
    public override string DefaultIndexKind => IndexKind.Hnsw;

    private readonly QdrantContainer _container = new QdrantBuilder().Build();
    private readonly bool _hasNamedVectors;
    private QdrantClient? _client;

    public QdrantClient Client => this._client ?? throw new InvalidOperationException("Not initialized");

    public QdrantVectorStore GetVectorStore(QdrantVectorStoreOptions options)
        => new(this.Client,
            ownsClient: false, // The client is shared, it's not owned by the vector store.
            new()
            {
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
        this.DefaultVectorStore = new QdrantVectorStore(this._client, ownsClient: false, new() { HasNamedVectors = this._hasNamedVectors });
    }

    protected override async Task StopAsync()
    {
        this._client?.Dispose();
        await this._container.StopAsync();
    }
}
