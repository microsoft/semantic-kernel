// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Options when creating a <see cref="PostgresVectorStore"/>.
/// </summary>
public sealed class PostgresVectorStoreOptions
{
    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string Schema { get; set; } = "public";

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
