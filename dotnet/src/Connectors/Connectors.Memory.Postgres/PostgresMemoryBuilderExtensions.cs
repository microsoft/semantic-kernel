// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Postgres connector.
/// </summary>
public static class PostgresMemoryBuilderExtensions
{
    /// <summary>
    /// Registers Postgres memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithPostgresMemoryStore(
        this MemoryBuilder builder,
        string connectionString,
        int vectorSize,
        string schema = PostgresMemoryStore.DefaultSchema,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IMemoryStore>(serviceId, (_, _) =>
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
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithPostgresMemoryStore(
        this MemoryBuilder builder,
        NpgsqlDataSource dataSource,
        int vectorSize,
        string schema = PostgresMemoryStore.DefaultSchema,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IMemoryStore>(serviceId, (_, _) =>
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
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including Postgres memory connector.</returns>
    public static MemoryBuilder WithPostgresMemoryStore(
        this MemoryBuilder builder,
        IPostgresDbClient postgresDbClient,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IMemoryStore, PostgresMemoryStore>(serviceId);

        return builder;
    }
}
