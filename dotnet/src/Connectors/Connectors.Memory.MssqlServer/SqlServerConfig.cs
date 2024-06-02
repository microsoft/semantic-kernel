// Copyright (c) Kevin BEAUGRAND. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.MssqlServer;

/// <summary>
/// Configuration for the SQL Server memory store.
/// </summary>
public class SqlServerConfig
{
    /// <summary>
    /// The default SQL Server collections table name.
    /// </summary>
    internal const string DefaultMemoryCollectionTableName = "SKMemoryCollections";

    /// <summary>
    /// The default SQL Server memories table name.
    /// </summary>
    internal const string DefaultMemoryTableName = "SKMemories";

    /// <summary>
    /// The default SQL Server embeddings table name.
    /// </summary>
    internal const string DefaultEmbeddingsTableName = "SKEmbeddings";

    /// <summary>
    /// The default schema used by the SQL Server memory store.
    /// </summary>
    public const string DefaultSchema = "dbo";

    /// <summary>
    /// The connection string to the SQL Server database.
    /// </summary>
    public string ConnectionString { get; set; } = null!;

    /// <summary>
    /// The schema used by the SQL Server memory store.
    /// </summary>
    public string Schema { get; set; } = DefaultSchema;

    /// <summary>
    /// The SQL Server collections table name.
    /// </summary>
    public string MemoryCollectionTableName { get; set; } = DefaultMemoryCollectionTableName;

    /// <summary>
    /// The SQL Server memories table name.
    /// </summary>
    public string MemoryTableName { get; set; } = DefaultMemoryTableName;

    /// <summary>
    /// The SQL Server embeddings table name.
    /// </summary>
    public string EmbeddingsTableName { get; set; } = DefaultEmbeddingsTableName;
}
