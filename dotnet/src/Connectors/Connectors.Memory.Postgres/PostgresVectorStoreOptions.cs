// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Options when creating a <see cref="PostgresVectorStore"/>.
/// </summary>
public sealed class PostgresVectorStoreOptions
{
    /// <summary>
    /// Gets or sets the embedding generator to use by default for vector properties in this vector store.
    /// </summary>
    /// <remarks>
    /// TODO
    /// </remarks>
    // TODO: Change type from object? to non-generic IEmbeddingGenerator once MEAI is updated.
    public object? EmbeddingGenerator { get; init; }

    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string Schema { get; init; } = "public";

    /// <summary>
    /// An optional factory to use for constructing <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    [Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
    public IPostgresVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
