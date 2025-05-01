// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Options when creating a <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class PostgresVectorStoreRecordCollectionOptions<TRecord>
{
    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string Schema { get; init; } = "public";

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreKeyPropertyAttribute"/>, <see cref="VectorStoreDataPropertyAttribute"/> and <see cref="VectorStoreVectorPropertyAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

    /// <summary>
    /// Gets or sets the default embedding generator for vector properties in this collection.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
