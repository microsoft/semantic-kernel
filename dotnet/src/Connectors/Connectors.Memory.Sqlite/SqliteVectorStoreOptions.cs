// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Options when creating a <see cref="SqliteVectorStore"/>.
/// </summary>
public sealed class SqliteVectorStoreOptions
{
    internal static readonly SqliteVectorStoreOptions Default = new();

    /// <summary>
    /// SQLite extension name for vector search operations.
    /// If not specified, the default "vec0" extension name will be used.
    /// More information here: <see href="https://github.com/asg017/sqlite-vec"/>.
    /// </summary>
    public string? VectorSearchExtensionName { get; set; }

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
