// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Options when creating a <see cref="WeaviateVectorStore"/>.
/// </summary>
public sealed class WeaviateVectorStoreOptions
{
    internal static readonly WeaviateVectorStoreOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateVectorStoreOptions"/> class.
    /// </summary>
    public WeaviateVectorStoreOptions()
    {
    }

    internal WeaviateVectorStoreOptions(WeaviateVectorStoreOptions? source)
    {
        this.Endpoint = source?.Endpoint;
        this.ApiKey = source?.ApiKey;
        this.HasNamedVectors = source?.HasNamedVectors ?? Default.HasNamedVectors;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Weaviate endpoint for remote or local cluster.
    /// </summary>
    public Uri? Endpoint { get; set; }

    /// <summary>
    /// Weaviate API key.
    /// </summary>
    /// <remarks>
    /// This parameter is optional because authentication may be disabled in local clusters for testing purposes.
    /// </remarks>
    public string? ApiKey { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector in Weaviate collection.
    /// Defaults to multiple named vectors.
    /// <see href="https://weaviate.io/developers/weaviate/config-refs/schema/multi-vector"/>.
    /// </summary>
    public bool HasNamedVectors { get; set; } = true;

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
