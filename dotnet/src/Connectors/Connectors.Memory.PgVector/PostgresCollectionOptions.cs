// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Options when creating a <see cref="PostgresCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class PostgresCollectionOptions
{
    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string Schema { get; set; } = "public";

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreKeyAttribute"/>, <see cref="VectorStoreDataAttribute"/> and <see cref="VectorStoreVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; set; }

    /// <summary>
    /// Gets or sets the default embedding generator for vector properties in this collection.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether the data source should be disposed after the collection is disposed.
    /// </summary>
    internal bool OwnsDataSource { get; set; }
}
