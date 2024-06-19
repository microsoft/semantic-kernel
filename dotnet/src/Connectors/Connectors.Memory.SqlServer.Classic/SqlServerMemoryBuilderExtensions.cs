// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.SqlServer.Classic;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure SQL Server or Azure SQL connector.
/// </summary>
public static class SqlServerMemoryBuilderExtensions
{
    /// <summary>
    /// Registers MSSQL Server.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="connectionString">Database connection string.</param>
    /// <param name="config">Configuration for the SQL Server connector.</param>
    /// <returns>Updated Memory builder including SQL Server memory connector.</returns>
    public static MemoryBuilder WithSqlServerClassicMemoryStore(
        this MemoryBuilder builder,
        string connectionString,
        SqlServerClassicConfig? config)
    {
        return builder.WithMemoryStore<SqlServerMemoryStore>(_ => new SqlServerMemoryStore(connectionString, config));
    }
}
