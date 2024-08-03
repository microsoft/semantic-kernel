// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure SQL Server or Azure SQL connector.
/// </summary>
public static class SqlServerMemoryBuilderExtensions
{
    /// <summary>
    /// Registers SQL Server or Azure SQL connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="connectionString">Database connection string.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithSqlServerMemoryStore(
        this MemoryBuilder builder,
        string connectionString,
        string schema = SqlServerMemoryStore.DefaultSchema)
    {
        return builder.WithMemoryStore(_ => new SqlServerMemoryStore(connectionString, schema));
    }
}
