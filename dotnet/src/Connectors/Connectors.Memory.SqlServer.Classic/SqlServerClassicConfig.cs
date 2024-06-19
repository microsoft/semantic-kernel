// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.SqlServer.Classic;

/// <summary>
/// Configuration for the SQL Server memory store.
/// </summary>
public class SqlServerClassicConfig
{
    /// <summary>
    /// The default SQL Server memories table name.
    /// </summary>
    internal const string DefaultMemoryTableNamePrefix = "SKMemories";

    /// <summary>
    /// The default SQL Server embeddings table name.
    /// </summary>
    internal const string DefaultEmbeddingsTableNamePrefix = "SKEmbeddings";

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
    /// The SQL Server memories table name prefix.
    /// When creating a collection, real table name will be '{CollectionTableNamePrefix}_{CollectionName}'.
    /// </summary>
    public string CollectionTableNamePrefix { get; set; } = DefaultMemoryTableNamePrefix;

    /// <summary>
    /// The SQL Server embeddings table name prefix.
    /// When creating a collection, real table name will be '{EmbeddingsTableNamePrefix}_{CollectionName}'.
    /// </summary>
    public string EmbeddingsTableNamePrefix { get; set; } = DefaultEmbeddingsTableNamePrefix;
}
