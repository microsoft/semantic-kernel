﻿// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Options when creating a <see cref="SqliteVectorStore"/>.
/// </summary>
public sealed class SqliteVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    public ISqliteVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }

    /// <summary>
    /// SQLite extension name for vector search operations.
    /// </summary>
    public string? VectorSearchExtensionName { get; set; } = null;

    /// <summary>
    /// Custom virtual table name to store vectors.
    /// </summary>
    /// <remarks>
    /// If not provided, collection name with prefix will be used as virtual table name.
    /// </remarks>
    public string? VectorVirtualTableName { get; set; } = null;
}