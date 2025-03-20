// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Memory;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

#pragma warning disable SKEXP0001

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Postgres connector.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PostgresVectorStore")]
public static class PostgresMemoryBuilderExtensions
{
    /// <summary>
    /// Registers Postgres memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithPostgresMemoryStore(
        this MemoryBuilder builder,
        string connectionString,
        int vectorSize,
        string schema = PostgresMemoryStore.DefaultSchema)
    {
        builder.WithMemoryStore((_) =>
        {
            return new PostgresMemoryStore(connectionString, vectorSize, schema);
        });

        return builder;
    }

    /// <summary>
    /// Registers Postgres memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithPostgresMemoryStore(
        this MemoryBuilder builder,
        NpgsqlDataSource dataSource,
        int vectorSize,
        string schema = PostgresMemoryStore.DefaultSchema)
    {
        builder.WithMemoryStore((_) =>
        {
            return new PostgresMemoryStore(dataSource, vectorSize, schema);
        });

        return builder;
    }

    /// <summary>
    /// Registers Postgres memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="postgresDbClient">Postgres database client.</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithPostgresMemoryStore(
        this MemoryBuilder builder,
        IPostgresDbClient postgresDbClient)
    {
        builder.WithMemoryStore((_) =>
        {
            return new PostgresMemoryStore(postgresDbClient);
        });

        return builder;
    }
}
