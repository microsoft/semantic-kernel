// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

#pragma warning disable SKEXP0001

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure SQL Server or Azure SQL connector.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and SqlServerVectorStore")]
public static class SqlServerMemoryBuilderExtensions
{
    /// <summary>
    /// Registers SQL Server or Azure SQL connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="connectionString">Database connection string.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <param name="embeddingDimensionsCount">Number of dimensions that stored embeddings will use</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithSqlServerMemoryStore(
        this MemoryBuilder builder,
        string connectionString,
        string schema = SqlServerMemoryStore.DefaultSchema,
        int embeddingDimensionsCount = SqlServerMemoryStore.DefaultEmbeddingDimensionsCount)
    {
        return builder.WithMemoryStore(_ => new SqlServerMemoryStore(connectionString, schema, embeddingDimensionsCount));
    }
}
