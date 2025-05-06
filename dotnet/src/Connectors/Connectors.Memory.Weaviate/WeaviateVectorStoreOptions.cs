// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Options when creating a <see cref="WeaviateVectorStore"/>.
/// </summary>
public sealed class WeaviateVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="WeaviateVectorStoreRecordCollection{TKey, TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    [Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
    public IWeaviateVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }

    /// <summary>
    /// Weaviate endpoint for remote or local cluster.
    /// </summary>
    public Uri? Endpoint { get; set; } = null;

    /// <summary>
    /// Weaviate API key.
    /// </summary>
    /// <remarks>
    /// This parameter is optional because authentication may be disabled in local clusters for testing purposes.
    /// </remarks>
    public string? ApiKey { get; set; } = null;

    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector in Weaviate collection.
    /// Defaults to multiple named vectors.
    /// <see href="https://weaviate.io/developers/weaviate/config-refs/schema/multi-vector"/>.
    /// </summary>
    public bool HasNamedVectors { get; set; } = true;

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
