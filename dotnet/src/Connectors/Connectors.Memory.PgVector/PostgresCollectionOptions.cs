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
    /// Initializes a new instance of the <see cref="PostgresCollectionOptions"/> class.
    /// </summary>
    public PostgresCollectionOptions()
    {
    }

    internal PostgresCollectionOptions(PostgresCollectionOptions? source)
    {
        this.Schema = source?.Schema ?? PostgresVectorStoreOptions.Default.Schema;
        this.OwnsDataSource = source?.OwnsDataSource ?? PostgresVectorStoreOptions.Default.OwnsDataSource;
        this.VectorStoreRecordDefinition = source?.VectorStoreRecordDefinition;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string Schema { get; set; } = PostgresVectorStoreOptions.Default.Schema;

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
    /// Gets or sets a value indicating whether the data source must be disposed by the collection when the collection is disposed.
    /// </summary>
    public bool OwnsDataSource { get; set; } = PostgresVectorStoreOptions.Default.OwnsDataSource;
}
