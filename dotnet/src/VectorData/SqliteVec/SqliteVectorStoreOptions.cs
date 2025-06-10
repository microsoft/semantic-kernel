// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Options when creating a <see cref="SqliteVectorStore"/>.
/// </summary>
public sealed class SqliteVectorStoreOptions
{
    internal static readonly SqliteVectorStoreOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreOptions"/> class.
    /// </summary>
    public SqliteVectorStoreOptions()
    {
    }

    internal SqliteVectorStoreOptions(SqliteVectorStoreOptions? source)
    {
        this.VectorVirtualTableName = source?.VectorVirtualTableName;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Custom virtual table name to store vectors.
    /// </summary>
    /// <remarks>
    /// If not provided, collection name with prefix "vec_" will be used as virtual table name.
    /// </remarks>
    public string? VectorVirtualTableName { get; set; }

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
