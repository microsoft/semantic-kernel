// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Options when creating a <see cref="SqliteCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class SqliteCollectionOptions
{
    internal static readonly SqliteCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteCollectionOptions"/> class.
    /// </summary>
    public SqliteCollectionOptions()
    {
    }

    internal SqliteCollectionOptions(SqliteCollectionOptions? source)
    {
        this.VectorStoreRecordDefinition = source?.VectorStoreRecordDefinition;
        this.VectorVirtualTableName = source?.VectorVirtualTableName;
        this.VectorSearchExtensionName = source?.VectorSearchExtensionName;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

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

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
