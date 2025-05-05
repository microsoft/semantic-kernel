﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Options when creating a <see cref="QdrantCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class QdrantCollectionOptions
{
    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector per qdrant point.
    /// Defaults to single vector per point.
    /// </summary>
    public bool HasNamedVectors { get; set; } = false;

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreKeyAttribute"/>, <see cref="VectorStoreDataAttribute"/> and <see cref="VectorStoreVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

    /// <summary>
    /// Gets or sets the default embedding generator for vector properties in this collection.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
