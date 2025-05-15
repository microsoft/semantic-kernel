// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Options when creating a <see cref="SqliteCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class SqliteCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly SqliteCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteCollectionOptions"/> class.
    /// </summary>
    public SqliteCollectionOptions()
    {
    }

    internal SqliteCollectionOptions(SqliteCollectionOptions? source) : base(source)
    {
        this.VectorVirtualTableName = source?.VectorVirtualTableName;
        this.VectorSearchExtensionName = source?.VectorSearchExtensionName;
    }

    /// <summary>
    /// SQLite extension name for vector search operations.
    /// </summary>
    public string? VectorSearchExtensionName { get; set; }

    /// <summary>
    /// Custom virtual table name to store vectors.
    /// </summary>
    /// <remarks>
    /// If not provided, collection name with prefix will be used as virtual table name.
    /// </remarks>
    public string? VectorVirtualTableName { get; set; }
}
