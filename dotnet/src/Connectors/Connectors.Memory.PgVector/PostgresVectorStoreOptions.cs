// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Options when creating a <see cref="PostgresVectorStore"/>.
/// </summary>
public sealed class PostgresVectorStoreOptions
{
    internal static readonly PostgresVectorStoreOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreOptions"/> class.
    /// </summary>
    public PostgresVectorStoreOptions()
    {
    }

    internal PostgresVectorStoreOptions(PostgresVectorStoreOptions? source)
    {
        this.Schema = source?.Schema ?? Default.Schema;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string Schema { get; set; } = "public";

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
