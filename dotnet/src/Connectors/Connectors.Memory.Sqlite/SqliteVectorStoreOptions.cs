// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Options when creating a <see cref="SqliteVectorStore"/>.
/// </summary>
public sealed class SqliteVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="SqliteVectorStoreRecordCollection{TKey, TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    [Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
    public ISqliteVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }

    /// <summary>
    /// SQLite extension name for vector search operations.
    /// If not specified, the default "vec0" extension name will be used.
    /// More information here: <see href="https://github.com/asg017/sqlite-vec"/>.
    /// </summary>
    public string? VectorSearchExtensionName { get; set; } = null;

    /// <summary>
    /// Custom virtual table name to store vectors.
    /// </summary>
    /// <remarks>
    /// If not provided, collection name with prefix "vec_" will be used as virtual table name.
    /// </remarks>
    public string? VectorVirtualTableName { get; set; } = null;

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
