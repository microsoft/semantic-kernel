// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Options when creating a <see cref="WeaviateVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class WeaviateVectorStoreRecordCollectionOptions<TRecord>
{
    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and Weaviate record.
    /// </summary>
    [Obsolete("Custom mappers are no longer supported.", error: true)]
    public IVectorStoreRecordMapper<TRecord, JsonObject>? JsonObjectCustomMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

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
